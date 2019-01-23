#### Sample API Result

This utility allows for Jobs to be scheduled and executed.

To Run the utility:
 - Copy `template.env` to `.env`
 - Make changes to the default values in `.env`
 - run `docker-compose up`
 - visit `http://localhost:{PORT}` with the port value from `.env`

Gotchas:
 - If you want persistence when you destroy the container, you need to mount `/datastore.db` from the container. 

Currently the only Job type available is a REST Proxy which takes the result of one REST call and sends data to another endpoint. All of this is highly configurable, and limited manipulation of data is possible between the calls. Pagination and other high value features are supported.

For the whole configuration specification, please refer to `schema.json`

A Job configuration will look something like this:

_This one gets current train locations in the Washington DC subway and send them as individual entities to Aether._

```json
{
  "id": "GetFromWMATA2",
  "owner": "shawn",
  "constants": {
    "api_key": "my source api key",
    "projectschema": "a variable for my output system",
    "contentType": "json",
    "status": "Publishable"
  },
  "source_url": "https://api.wmata.com/TrainPositions/TrainPositions",
  "source_type": "GET",
  "source_headers": [
    "api_key"
  ],
  "source_query_params": [
    "contentType"
  ],
  "source_msg_path": "$.TrainPositions[*]",
  "source_datamap": {
    "api_key": "$.constants.api_key",
    "contentType": "$.constants.contentType"
  },
  "dest_type": "POST",
  "dest_url": "http://kernel.aether.local:8000/entities/",
  "dest_basic_auth": {
    "user": "admin",
    "password": "adminadmin"
  },
  "dest_datamap": {
    "id": "$.resource._builtins.uuid",
    "payload": "$.msg",
    "payload.id" : "$.resource._builtins.uuid",
    "payload.time": "$.resource._builtins.now",
    "projectschema": "$.constants.projectschema",
    "status": "$.constants.status"
  },
  "dest_json_body": [
    "id",
    "payload",
    "payload.id",
    "payload.time",
    "projectschema",
    "status"
  ]
}
```

For a simple explantaion, look at the following. An individual REST response like this could trigger three calls to be made, if `source_msg_path` were set to `$.messages`, which is the jsonpath of an iterable resource. Additionally, setting `source_pagination_url`, would inform the utility to continue onto subsequent available pages.

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