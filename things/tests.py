from django.test import TestCase
from django.db.utils import IntegrityError
from .models import World

class BaseWorldTest(TestCase):
    def setUp(self):
        pass

class TestModelWorld(BaseWorldTest):
    def test_world_sun_power_positive(self):
        with self.assertRaises(IntegrityError):
            w = World(sun_power=0.0)
            w.save()

    def test_world_entropy_lower_than_one(self):
        with self.assertRaises(IntegrityError):
            w = World(entropy=1.0)
            w.save()

    def test_world_entropy_greater_than_zero(self):
        with self.assertRaises(IntegrityError):
            w = World(entropy=0.0)
            w.save()
