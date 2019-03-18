DynamicPublisher
=========
The DynamicPublisher block sends signals to a dynamic topic. The topic expression is evaulated for _each_ signal, and the resulting topic is used to publish. The entire signal must be JSON-serializable. 

For more information on publishing to topics, view the [pub/sub docs.](https://docs.n.io/service-design-patterns/pub-sub.html)

Properties
----------
- **Topic**: Hierarchical topic expression to publish the incoming signals to. 

Advanced Properties
---

- **Time-to-live**: Time-to-live for each published **topic**. If no signals have been received for this **topic** within the **ttl** window, then the Publisher is eligible for removal/garbage-collection.
- **Local Publisher?**: Configure this DynamicPublisher to act like a LocalPublisher block—can send data to the LocalSubscriber blocks on the same instance.
- **Local Identifier**: Override the local identifier for local publishers. This value is only applicable when **Local Publisher?** is enabled.

  Note: If the *Time-to-live* is a negative value, then the published topics will *never* expire.

Examples
---

##### Basic Usage

You can use a DynamicPublisher block to publish a signal to a topic that is derived from the incoming signal. Consider the following `DynamicPublisher` configuration:

```yaml
topic: "airports.{{ $code }}.temperature"
```


Passing in a signal `{ "code": "DEN", "temp": "26.4" }` will publish it to the topic `airports.DEN.temperature`. If that publisher doesn't already exist, it will be created, otherwise the existing publisher will be reused.


##### Signal Grouping 

The DynamicPublisher block will also group incoming signals by topic before publishing:

```yaml
topic: "data.{{ $group }}"
```

```text
[
  { "group": "foo", "data": 1 },
  { "group": "bar", "data": 2 },
  { "group": "baz", "data": 3 },
  { "group": "foo", "data": 4 },
  { "group": "bar", "data": 5 },
  { "group": "foo", "data": 6 }
]
```

These signals will be grouped into three groups that will be published:

```
[
  { "group": "foo", "data": 1 },
  { "group": "foo", "data": 4 },
  { "group": "foo", "data": 6 }
] => Publisher("data.foo")
```

```
[
  { "group": "bar", "data": 2 },
  { "group": "bar", "data": 5 }
] => Publisher("data.bar")
```

```
[
  { "group": "baz", "data": 3 }
] => Publisher("data.baz")
```


##### Signal Fan-Out

You can implement a fan-out by using a random expression to publish to.

```yaml
topic: "queues.process.{{ random.randint(1,4) }}"
```

Notes
---

If your topic is static then consider using the [Publisher](publisher.md) or [LocalPublisher](local_publisher.md) blocks instead.
