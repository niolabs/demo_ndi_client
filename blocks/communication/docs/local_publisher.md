LocalPublisher
==============
The LocalPublisher publishes incoming signals to the configured topic. Only LocalSubscriber blocks on the same nio instance can subscribe to this data. Signals will be pickled before publishing, so unlike the "regular" Publisher the entire signal does not need to be JSON-serializable.

For more information on publishing to topics, view the [pub/sub docs.](https://docs.n.io/service-design-patterns/pub-sub.html)

Properties
----------
- **Topic**: Hierarchical topic string to publish to.
