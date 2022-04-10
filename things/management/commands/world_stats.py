from django.core.management.base import BaseCommand, CommandError
from things.models import World

class Command(BaseCommand):
    help = 'Prints world statistics'


    def add_arguments(self, parser):
        parser.add_argument('--world_id', nargs='?', default=1, type=int)

    def handle(self, *args, **options):
        world_id = options['world_id']
        try:
            world = World.objects.get(pk=world_id)
        except World.DoesNotExist:
            raise CommandError('World "%s" does not exist' % world_id)

        self.stdout.write(self.style.SUCCESS(
            f"Statistics of World {world_id}"
        ))
        self.stdout.write(self.style.SUCCESS(
            f"\tTotal things born: {world.moss_set.all().count()}"
        ))
        self.stdout.write(self.style.NOTICE(
            f"\tTotal things alive: {world.moss_set.filter(alive=True).count()}"
        ))
        self.stdout.write(self.style.WARNING(
            f"\tTotal things dead: {world.moss_set.filter(alive=False).count()}"
        ))

        
