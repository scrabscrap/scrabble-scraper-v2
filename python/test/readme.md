# Tests - in general

Threads should not be used in the tests. Usually the class under test can instanciated 
directly.

An integration test can be performed using mock hardware and triggered by button events.
It must be ensured that the thread pool is cleaned up correctly at the end of the 
test. For further test, the pool and the mock objects has to be recreated.
