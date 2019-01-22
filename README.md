#### Sample API Result

```json
{
  "count": 3,
  "url": "http://api.com/?page=2",
  "previous": "http://api.com/?page=1",
  "next": "http://api.com/?page=3",
  "messages":[
    {"id": 1},
    {"id": 2},
    {"id": 3}
  ]
}
```

#### Sample Message Context for Message 1
```json
{
  "constant": {"": ""},
  "context": {
    "count": 3,
    "url": "http://api.com/?page=2",
    "previous": "http://api.com/?page=1",
    "next": "http://api.com/?page=3",
    "messages":[
      {"id": 1},
      {"id": 2},
      {"id": 3}
    ]
  },
  "msg": {"id": 1}
}
```