from django.core.management.base import BaseCommand, CommandError
from things.models import World

class Command(BaseCommand):
    help = 'Advances world with n steps'


    def add_arguments(self, parser):
        parser.add_argument('--world_id', nargs='?', default=1, type=int)
        parser.add_argument('--nsteps', nargs='?', default=1, type=int)


    def handle(self, *args, **options):
        world_id = options['world_id']
        nsteps = options['nsteps']
        try:
            world = World.objects.get(pk=world_id)
        except World.DoesNotExist:
            raise CommandError('World "%s" does not exist' % world_id)

        print(f"Executing {nsteps} steps on World {world_id}")
        world.step(nsteps)
