# nio Service Unit Tests

A testing framework for writing and running unit tests for nio services.

## How to Use

Clone this repo into your nio project directory as a submodule
```
git submodule add https://github.com/nioinnovation/service_tests.git
```
Then create a **tests** directory for your service unit tests.
```
mkdir tests && touch tests/__init__.py
```
Example project file structure:

```
- nio.env
- nio.conf
- etc/
- blocks/
- tests/
  - __init__.py
- service_tests/
  - service_test_case.py
...
```

If you cloned the project template repo from [https://github.com/nioinnovation/project_template](https://github.com/nioinnovation/project_template) at the start of your project, this will already be set up for you.

Install _jsonschema_ for publisher/subscriber topic validation.

```
pip3 install jsonschema
```

## Setting Up Your Test Class

Generally speaking, you will have a service test file (and class) for each service. You can use the following example as starting point for your service unit test files:

```python
from nio.signal.base import Signal
from .service_test_case import NioServiceTestCase


class TestExampleService(NioServiceTestCase):

    service_name = "ExampleService"

    def subscriber_topics(self):
        """Topics this service subscribes to"""
        return ['topic1', 'topic2']

    def publisher_topics(self):
        """Topics this service publishes to"""
        return ['topic3']

    def env_vars(self):
        """Environment variables"""
        return {
            "TEST_VARIABLE": "test variable"
        }

    def test_service(self):
        topic1 = self.subscriber_topics()[0]
        self.publish_signals(topic1, [Signal({
            "data": self.env_vars()["TEST_VARIABLE"]
        })])
        self.assert_num_signals_published(1)
        self.assert_signal_published({
            "data": "test variable"
        })
```

Each test class can only contain unit tests for one service. These unit tests are not meant for testing interaction between services. Testing interactions between services would be integration testing.

**Set `service_name` Class Attribute**<br>The very first thing to do is change the class attribute `service_name` from "ExampleService" to your service name. This is how the test will know which service and blocks to load and configure.

**Override `subscriber_topics` and `publisher_topics`**<br>If the service has subscriber or publisher blocks, override these methods to return a list of the topic names in your service. This allows your tests to publish test signals to the subscribers and to assert against the published signals from the service.

**Add `env_vars`**<br>These service tests will not read from any of your project `.env` files so if you want to use some environment variables, override this method and have it return a dictionary that maps environment variable names to values.

## Kicking Off Tests

If your service has blocks that generate signals on their own (e.g., simulator blocks), then the service will already be running with signals when each test is entered. However, it's easier to test services when you have control over the created signals.

You can create a signal and send it from any block with:

```python
self.notify_signals(block_name, signals)
```
You can create a signal and publish it to a topic to notify from the matching subscriber block(s) with:

```python
self.publish_signals(topic, signals)
```

## Making Assertions about Signals

Most service unit tests will be structured so that you publish or emit a signal from a block at the beginning of a service and then inspect the output at the end of the service. The easiest way to make these assertions is by checking which signals the service's publishers have published.

Get published signals with:

```python
self.published_signals()
```

Get processed signals with:

```python
self.processed_signals()["block_name"]
```

Most blocks also support the ability to fake time so you can jump ahead in time to check signals. For example, a _SignalTimeout_ block may be configured to notify a timeout signal after 10 seconds. Instead of making your test take 10 seconds, jump ahead in time with

```python
self._scheduler.jump_ahead(seconds=10)
```


## Asynchronous Service Tests

There is an option to run the service tests asynchronously by setting the class attribute `synchronous=False`.
This will run the service as it would on an actual nio instance. Because of this behavior, some waiting is required
to make sure that signals get to their destination before doing assertions on them.

### Waiting for Signals (Asynchronous)

Wait for signals to be published with:

```python
# count: number of cumulative signals to wait for since the service started
# timeout: time in seconds to wait before returning, even if *count* has not been reached
wait_for_published_signals(count=0, timeout=1)
```

Another option is to wait for a block to process signals:

```python
wait_for_processed_signals(block, number, timeout)
```

## Subscriber/Publisher Topic Validation with _jsonschema_

You can also validate signals associated with publishers and subscribers by putting a JSON-schema formatted JSON file in one of three locations: `project_name/tests`, `project_name/`, or one directory above `project_name/`. For more information, see [http://json-schema.org/](http://json-schema.org/) and [https://spacetelescope.github.io/understanding-json-schema/UnderstandingJSONSchema.pdf](https://spacetelescope.github.io/understanding-json-schema/UnderstandingJSONSchema.pdf).

Signals published to the specified topics will be validated according to the file specification.

For instance, this JSON schema will make sure that all signals published to the topic "test_topic" are dictionary objects with at least one property. All signals going into this topic are required to have a "test_attribute" attribute, which can be a string or integer. Any additional properties on the signal must be of type integer.

```python
{
  "test_topic": {
    "type": "object",
    "minProperties": 1,
    "properties": {
      "test_attribute": {"type": ["string", "integer"],
                         "minlength": 1}
    },
    "required": ["test_attribute"],
    "additionalProperties": {"type": "integer"}
  }
}
```

## Test

Execute the service tests using a Python test runner.
```python
py.test tests
```
