import random
import logging
from typing import final
from django.db import models, transaction
from django.core.validators import MaxValueValidator, MinValueValidator

logger = logging.getLogger(__name__)

_MIN_SUN_POWER = 1.0
_MIN_ENTROPY = 1.0/64.0
_MAX_ENTROPY = 1.0-_MIN_ENTROPY
_DEFAULT_SUN_POWER=2.0
_DEFAULT_ENTROPY=0.125


class Position(models.Model):
    x = models.IntegerField()
    y = models.IntegerField()
    def __str__(self):
        return f'({self.x}, {self.y})'
    class Meta:
        unique_together = [['x', 'y']]

class World(models.Model):
    sun_power = models.FloatField(
            default=_DEFAULT_SUN_POWER,
            validators=[MinValueValidator(_MIN_SUN_POWER)]
    )
    entropy = models.FloatField(
            default=_DEFAULT_ENTROPY,
            validators=[
                MinValueValidator(_MIN_ENTROPY),
                MaxValueValidator(_MAX_ENTROPY)
            ]
    )

    def get_energy(self, thing):
        pos = thing.position
        distance = (abs(pos.x) + abs(pos.y)) / 8.0
        occupation = thing.position.moss_set.count()
        effective_sun_power = self.sun_power / occupation / (1.0 + distance)
        logger.debug(f'Position {pos} is occupied by {occupation} things distant {distance} from center.')
        logger.debug(f'Resultuing energy: {effective_sun_power}')
        return effective_sun_power

    def step(self, num_steps=1):
        for n in range(num_steps):
            with transaction.atomic():
                for t in self.moss_set.filter(alive=True):
                    t.act()
                    t.eat()
                    t.son()
                    t.die()
                self.save()

    class Meta:
        # Check that world.energy * (1.0 - world.entropy) > 1.0
        # So sp > 1/(1-ent)
        constraints = [
                models.CheckConstraint(
                    check=models.Q(
                        sun_power__gt=(1.0/(1.0 - models.F('entropy')))
                    ),
                    name='enough_power_for_entropy'
                ),
                models.CheckConstraint(
                    check=models.Q(entropy__gt=0.0) & models.Q(entropy__lt=1.0),
                    name='entropy_between_0_and_1'
                ),
                models.CheckConstraint(
                    check=models.Q(sun_power__gt=0.0),
                    name='sun_power_positive'
                ),
        ]


class Thing(models.Model):
    world = models.ForeignKey(World, on_delete=models.CASCADE)
    alive = models.BooleanField(default=True)
    energy = models.FloatField(default=3.0, validators=[MinValueValidator(0.0)])
    min_energy_son = models.FloatField(default=4.0, validators=[MinValueValidator(0.0)])
    energy_son = models.FloatField(
        default=0.25,
        validators=[
            MinValueValidator(0.0),
            MaxValueValidator(1.0)]
    )
    position = models.ForeignKey(Position, on_delete=models.PROTECT)

    def __str__(self):
        return f'[id={self.pk}:alive={self.alive}:energy={self.energy}]@{self.position}'

    def act(self):
        raise NotImplementedError

    def eat(self):
        raise NotImplementedError

    def mutate(self):
        raise NotImplementedError

    def get_son(self):
        raise NotImplementedError

    @final
    def son(self):
        if self.energy > self.min_energy_son:
            son_energy = self.energy * self.energy_son
            self.energy -= son_energy
            son = self.get_son()
            son.mutate()
            son.energy = son_energy * (1.0 - self.world.entropy)
            son.save()
            logger.debug(f"{self} have a son: {son}")
            self.save()

    @final
    def die(self):
        if self.energy <= 0.0:
            self.alive = False
            self.save()
            logger.info(f"I have died: {self}")

    class Meta:
        abstract = True
        constraints = [
                models.CheckConstraint(
                    check=models.Q(energy__gte=0.0),
                    name='energy_positive'
                ),
                models.CheckConstraint(
                    check=models.Q(energy_son__gt=0.0) & models.Q(energy_son__lt=1.0),
                    name='energy_son_between_0_and_1'
                ),
                models.CheckConstraint(
                    check=models.Q(min_energy_son__gt=2.0),
                    name='min_energy_son_greater_than_two'
                ),
        ]


class Moss(Thing):
    spread = models.PositiveSmallIntegerField(default=1)

    def act(self):
        self.energy -= 1.0
        if self.energy < 0.0:
            self.energy = 0.0
        self.save()
        self.die()

    def eat(self):
        bite = self.world.get_energy(self)
        logger.debug(f'{self.pk}: I have bite: {bite}')
        self.energy += bite
        self.save()

    def get_son(self):
        dist = random.randint(1, self.spread)
        if random.random() >= 0.5:
            dist = -dist
        axis = random.randint(0,1)
        x = self.position.x
        y = self.position.y
        if axis:
            x += dist
        else:
            y += dist
        self.energy -= dist
        self.save()
        son_position = Position.objects.get_or_create(x=x, y=y)[0]
        logger.debug(f"Son position: {son_position}")
        son = Moss(
                energy=self.energy,
                world=self.world,
                min_energy_son=self.min_energy_son,
                energy_son=self.energy_son,
                position=son_position
        )
        return son

    def mutate(self):

        MUTATION_TYPE_MIN_ENERGY = 1
        MUTATION_TYPE_ENERGY_SON = 2

        MUTATION_TYPES = (
            MUTATION_TYPE_MIN_ENERGY,
            MUTATION_TYPE_ENERGY_SON
        )

        # mutation occurs sparingly
        mutate = random.random() > (1.0 - self.world.entropy)

        if mutate:
            mutation_type = random.randint(MUTATION_TYPES[0], MUTATION_TYPES[-1])
            match mutation_type:
                case [MUTATION_TYPE_MIN_ENERGY]:
                    # variate min_energy_son
                    self.min_energy_son += self.min_energy_son * self.world.entopy * (random.random() - 0.5)
                    if self.min_energy_son < 2.0:
                        self.min_energy_son = 2.0
                    return
                case [MUTATION_TYPE_ENERGY_SON]:
                    # variate energy_son
                    self.energy_son += self.energy_son * self.world.entopy * (random.random() - 0.5)
                    if self.energy_son <= 0.0:
                        self.energy_son = self.world.entropy
                    if self.energy_son >= 1.0:
                        self.energy_son = 1.0 - self.world.entropy
                    return
        else:
            return
