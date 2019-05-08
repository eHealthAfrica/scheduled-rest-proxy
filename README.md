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
  "source_headers": {
    "api_key": "$.constants.api_key"
  },
  "source_query_params": {
    "contentType": "$.constants.contentType"
  },
  "source_msg_path": "$.TrainPositions[*]",
  "dest_type": "POST",
  "dest_url": "http://kernel.aether.local:8000/entities/",
  "dest_basic_auth": {
    "user": "admin",
    "password": "adminadmin"
  },
  "dest_json_body": {
    "id": "$.resource._builtins.uuid",
    "payload": "$.msg",
    "payload.id" : "$.resource._builtins.uuid",
    "payload.time": "$.resource._builtins.now",
    "projectschema": "$.constants.projectschema",
    "status": "$.constants.status"
  }
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

#### Persisting Values Between Jobs

We can persist results from the query to use in future queries. In the configuration, we can setup persistence by adding a few options:

```python
{
  "initial_query_resources": {  # the initial value if no value is found in the database
    "modified__gt": "2019-02-27",
  },
  "query_resource": [  # the names of the expected resources
    "modified__gt"
  ],
  "dest_save_resource": {
    "modified__gt": "$.msg.modified"  # the new value from response messages to set to to the resource
  }
}
```

In this example, the intial job run can use the value we specify for `modified__gt` in `initial_query_resources`.

Any of the look-ups, header, json_body, post_body, etc, can get and use the persited value by referncing path:
`$.resource.modified__gt`

After we get a response, a new value for `modified__gt` will be copied from the message at path `$.msg.modified`.
A second job run will use the value saved in the database for the next request.

#### Building Jobs

For testing new configurations, it can be helpful to to make sure your requests are being properly formatted before there is an interaction with the server.

For requests to the source system, we can set the configuration:
```json 
{"source_mock_request": true}
```
This will show what the source request would have consisted of in the execution log for your job, but will not send the request to the source system. Without the source request, the destination request also will not be fired.

Likewise, if you want to query the source system and build your destination request, but you don't want to spam your destination system with test data while you work out the bugs, you can use a similar setting:
```json 
{"dest_mock_request": true}
```
Likewise, this will send the destination requests to the execution log for your job without sending the data to the destination system.
