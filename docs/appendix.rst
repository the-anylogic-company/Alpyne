
Appendix
========

This page will contain additional technical or supplementary information, expanding on the topics in the other pages.

Locking
-------
Of the endpoints exposed by the alpyne the server (the underlying executable running your simulation model), all but one are setup to return a response with as minimal overhead as possible.

Informational requests (e.g., getting the sim schema or current status) are queried and returned immediately, as they are not time consuming to execute. In contrast, requests to reset or take action cause the sim to run until the next action which, depending on the model, can take anything from milliseconds to minutes; the server's response to these requests are thus only based on whether the request was successfully validated.

Though, there is one endpoint whose request consists of a condition and a timeout; calling this endpoint consumes the request until the conditions of said request can be met or the timeout elapses -- in the Python library, this is referred to by "locking".

The condition is a flag for the underlying sim's engine to be in. This can be specified using the provided ``EngineState`` enum. The default is ``EngineState.ready()``, a shorthand for ``EngineState.PAUSED | EngineState.FINISHED | EngineState.ERROR`` - i.e., locking until paused (by a sim call to ``takeAction()``), finished (by a sim call to ``finishSimulation()`` or the stop condition being met when the constructor argument ``auto_finish`` is true), or errored (by a sim encountering a runtime error or a call to ``error(...)``).

The timeout is a number of (real world) seconds to wait for said condition to be met. By default, this is 30. This should be set based on the maximum (real world) time between actions with a plentiful amount of buffer.

