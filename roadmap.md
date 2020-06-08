Future Enhancements
===================

Some improvements I would like to make in the future:

- Look into adding some sliders to control test fixtures manually. This would
  require storing the state of fixtures at various scopes (session, module,
  function etc.) and preventing a fixture from being started again by pytest if
  it was already started manually.
- Support listening on port 0.

