LocalPublisher
==============
Publish input signals to the configured topic. Only LocalSubscriber blocks on the same nio instance can subscribe to this data. Unlike the regular Publisher block, these signals do not need to contain data this is valid JSON.

Properties
----------
- **local_identifier**: Unique identifier of this instance in the nio system.
- **topic**: Hierarchical topic string to publish to

Inputs
------
- **default**: Any list of signals.

Outputs
-------
None

Commands
--------
None

Dependencies
------------
None

LocalSubscriber
===============
Subscribe to the configured topic and output signals received. Only LocalSubscriber blocks on the same nio instance can subscribe to this data. Unlike the regular Publisher block, these signals do not need to contain data this is valid JSON.

Properties
----------
- **local_identifier**: Unique identifier of this instance in the nio system.
- **topic**: Hierarchical topic string to publish to

Inputs
------
None

Outputs
-------
- **default**: A signal of the message published to the configured topic.

Commands
--------
None

Dependencies
------------
None

Publisher
=========
Publish input signals to the configured topic

Properties
----------
- **topic**: Hierarchical topic string to publish to

Inputs
------
- **default**: Each input signal will be sent along to the appropriate Subscribers based on the *topic*.

Outputs
-------
None

Commands
--------
None

Dependencies
------------
None

Subscriber
==========
Subscribe to the configured topic and output signals received

Properties
----------
- **topic**: Hierarchical topic string to subscribe to

Inputs
------
None

Outputs
-------
- **default**: Signal list for each message received on topic

Commands
--------
None

Dependencies
------------
None

