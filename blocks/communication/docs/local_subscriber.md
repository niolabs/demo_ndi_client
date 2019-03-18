LocalSubscriber
===============
The LocalSubscriber block subscribes to the configured topic and outputs signals received. Only LocalPublisher blocks on the same nio instance can send data to the LocalSubscriber blocks.

For more information on subscribing to topics, view the [pub/sub docs.](https://docs.n.io/service-design-patterns/pub-sub.html)

Properties
----------
- **Topic**: Hierarchical topic string to subscribe to.
