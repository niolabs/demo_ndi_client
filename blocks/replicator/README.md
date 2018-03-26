Replicator
==========
Each incoming signal is replicated x times, where x is the number of items in the list that `list` evaluates to. Each output signal will be the same as the input signal with a new attribute, `title`, set to a value of the list.

Properties
----------
- **list**: An expression property that needs to evaluate to a list. A signal will be notified from the block for each item in the list.
- **title**: Name of attribute to be added with list value.

Inputs
------

Outputs
-------

Commands
--------

Example
-------
Block Config:
```
{
  'title': 'meal',
  'list': '{{ $meals }}'
}
```
Input Signal:
```
{
  'type': 'meal',
  'meals': ['pork chop', 'pizza', 'chicken']
}
```
3 Output Signals:
```
{
  'type': 'meal',
  'meals': ['pork chop', 'pizza', 'chicken'],
  'meal': 'pork chop'
}
{
  'type': 'meal',
  'meals': ['pork chop', 'pizza', 'chicken'],
  'meal': 'pizza'
}
{
  'type': 'meal',
  'meals': ['pork chop', 'pizza', 'chicken'],
  'meal': 'chicken'
}
```
