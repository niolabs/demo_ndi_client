Join
====
Group a list of input signals into one signal. The output signal will contain an attribute for each evaluated `key` and the `value` of the key will be a **list** containing each value with a matching key.

Properties
----------
- **enrich**: If true, the original incoming signal will be included in the output signal.
- **group_attr**: When `group_by` is used, this is the value that will be stored in a signal attribute called, in this case, `group`.
- **group_by**: Incoming signal attribute to group signals by.
- **key**: Evaluates to a key attribute on output signal.
- **one_value**: If true, each attribute on the output signal has a value that is a single item instead of a list of all matching values.
- **value**: Evaluates to a value in a list of values with a matching key.

Inputs
------
- **default**: Any list of signals.

Outputs
-------
- **default**: One output signal that has an attribute for each `key` and that attribute is a **list** containing a `value` for each matching key found in an input signal.

Commands
--------
- **groups**: Display a list of the signal groupings.

Examples
--------
**Input Signals**
```python
[
{ "type": "shirt", "color": "red", "size": 10},
{ "type": "shirt", "color": "red", "size": 14},
{ "type": "shirt", "color": "orange", "size": 12},
{ "type": "scarf", "color": "red", "size": "M"},
{ "type": "shoes", "color": "orange", "size": 8}
]
```
**Block Config with _key_ based on `type`**
```
key: {{ $type }},
value: {{ $size }},
one_value: False
```
**Output Signal**
```python
{
  "shoes": [8],
  "scarf": ["M"],
  "shirt": [10, 14, 12],
  "group": ""
}
```
**Block Config with _key_ based on `type` and enriching signals**
```
key: {{ $type }},
value: {{ $size }},
one_value: False
enrich.exclude_existing: False
```
**Output Signal**
```python
{
  "shoes": [8],
  "scarf": ["M"],
  "shirt": [10, 14, 12],
  "group": "",
  "type": "shoes",
  "color": "orange",
  "size": 8
}
```
**Block Config with _key_ based on `color`**
```
key: {{ $color }}
value: {{ $type }}
one_value: False
```
**Output Signal**
```python
{
  "orange": ["shirt", "shoes"],
  "red": ["shirt", "shirt", "scarf"],
  "group": ""
}
```
**Block Config with _key_ based on `color` and _One Value Per Key_ checked**
```
key: {{ $color }}
value: {{ $type }}
one_value: True
```
**Output Signal**
```python
{
  "red": "scarf",
  "orange": "shoes",
  "group": ""
}
```
**Block Config using `group_by` to spit out multiple signals**
```
key: {{ $type }}
value: {{ $size }}
group_by: {{ $color }}
one_value: False
```
**Output Signals (one for each value of `color`)**
```python
[
  {"group": "orange", "shoes": [8], "shirt": [12]},
  {"group": "red", "scarf": ["M"], "shirt": [10, 14]}
]
```

***
