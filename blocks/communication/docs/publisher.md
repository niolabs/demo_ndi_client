Publisher
=========
The Publisher block sends signals to the configured static topic. Publisher blocks can send signals on a configured topic to a subscriber block in any instance within the same system. The entire signal must be JSON-serializable. For signals that cannot be represented in JSON, use a LocalPublisher if appropriate or Pickle signals before publishing.

For more information on publishing to topics, view the [pub/sub docs.](https://docs.n.io/service-design-patterns/pub-sub.html)

Properties
----------
- **Topic**: Hierarchical topic string to publish to.

Notes
---

If you need to publish signals to a topic that derived from properties on the incoming signals, then use the a [DynamicPublisher](dynamic_publisher.md) block instead.
