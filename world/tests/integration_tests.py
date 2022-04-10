import pytest
import random
import logging
from things.models import World, Moss, Position

logger = logging.getLogger(__name__)

@pytest.fixture
def setup_random():
    return random.seed(123456789)

def test_seed(setup_random):
    assert random.random() == 0.6414006161858726

@pytest.mark.django_db(transaction=True)
def test_world_step(setup_random, caplog):
    caplog.set_level(logging.DEBUG)
    center = Position(x=0, y=0)
    center.save()
    w = World(sun_power=1.125, entropy=0.0625)
    m = Moss(world=w, energy=9.0, min_energy_son=10.0, position=center, spread=4)
    w.save()
    m.save()
    logger.info(f'Stepping with initial Moss: {m}')
    w.step()
    logger.info(f'Stepped with final Mosses: {w.moss_set.filter(alive=True)}')
    w.step(40)
    logger.info(f'Stepped with final Mosses: {w.moss_set.all()}')
    assert w.moss_set.count() == 3
