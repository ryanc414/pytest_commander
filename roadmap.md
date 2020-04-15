Future Enhancements
===================

Some improvements I would like to make in the future:

- Run the tests in one (or more) separate worker processes on the backend.
  Currently both the tests and HTTP/websocket server are run in the same process,
  which means that HTTP and websocket requests will not be processed while
  tests are running (which could take a while).
- Look into adding some sliders to control test fixtures manually. This would
  require storing the state of fixtures at various scopes (session, module,
  function etc.) and preventing a fixture from being started again by pytest if
  it was already started manually.
- Listen on 0.0.0.0 so that the app can be accessed remotely.
- Support listening on port 0.

