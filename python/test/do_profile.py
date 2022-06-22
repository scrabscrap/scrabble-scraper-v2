import cProfile
import unittest

if __name__ == '__main__':
    suite = unittest.TestLoader().discover('.')
    def runtests():
      unittest.TextTestRunner().run(suite)

    with cProfile.Profile() as pr:
        pr.enable()
        pr.run('runtests()')
        pr.disable()
        pr.create_stats()
        pr.print_stats(sort='cumtime')
        pr.dump_stats('unittest-profile.prof')
