
Appendix
========

Data storage format
--------------------
In each of version templates (inputs, outputs, Configuration, Observation, and Action), each data element is stored as a dictionary containing the keys: name, type, value, units. 

name
  The label you set within your model. For inputs and outputs, these are the variable names you set after dragging the related objects into your agent. For the three RL spaces, these are the names you set under the respective tables in the RL experiment's properties. In addition, inputs and Configuration have engine settings (see ``alpyne.data.constants.EngineSettings``).

type
  String constants reflecting the assigned data types (see ``alpyne.data.constants.InputTypes`` and ``alpyne.data.constants.OutputTypes``). The data types are enforced, with certain exceptions (see following section).
  
value
  The current value for the data element. For user-defined entries in template objects, these will be set to their Java default values (0 for numerical types, null for objects). Engine settings will have the settings set in the experiment properties. 
  
units
  The data units for the element or ``null`` / ``None`` for unit-less types.
  
For convenience, special Python methods have been overriden to allow you to query and modify these data elements by directly accessing the attributes in one of the space objects. Alternatively, you can use the ``get_inputs`` and ``set_inputs`` methods.
  
  
Overriding pre-implemented methods in ``BaseAlpyneEnv``
--------------------------------------------------------

The ``BaseAlpyneEnv`` class subclasses Gym's base environment class and as such, it implements the methods required with custom gym environments - namely ``step``, ``reset``, and ``render``. The basic logic of each is routine and doesn't depend on model being used. However, some of the more nuanced logic involved with each is not able to be made generic. This includes describing the bounds of the observation or action space and converting Alpyne's relevant object types (Observation and Action) to Python types compatible with the Gym interface. For these, there are abstract methods you implement. This is described in more detailed in the relevant class documentation.

The ``step``, ``reset``, and ``render`` methods are implemented in a "bare-bones" way, only consisting of the minimum code required to fulfill the method's purpose. In some cases, it might be desired to add your own custom logic on top of this! For example, maybe you want to write some outputs to a file on each step or change how the environment is rendered.

Similar to how you override the abstract methods, you can also override the methods defined in the base class. This will work as long as you preserve the same method name, arguments, and return values. For the latter, the most efficient way to do this is to call the same-named method of ``super()``.

The following shows an example of adding logic to the ``step`` method and replacing the default ``render`` method. The initialization method (``__init__``) is also overridden so that a class-variable can be added.

::

	class MyAnyLogicEnv(BaseAlpyneEnv):
		def __init__(self, sim):
			""" Add custom class-variables to the class """
			super().__init__(sim)  # initialize with the code from the original base class
			self.last_sequence = (None, None, None) # (observation, action, reward)
	
		#
		# implementation of the four required abstract methods have been omitted for brevity
		#
		
		def step(self, action):
			""" Add custom file logging *on top of* the BaseAlpyneEnv's ``step`` method """
			# log pre-action observation + the impending action
			old_obs = self.sim.get_observation()
			with open("sim.log", "a") as outfile:
				outfile.write( f"Observation: {old_obs}\n" )
				outfile.write( f"Action     : {action}\n" )
			
			# now call parent ``step`` method to proceed normally, capturing its return
			new_obs, reward, done, info = super().step(action)
			
			# log result of action
			with open("sim.log", "a") as outfile:
				outfile.write( f"Reward     : {reward}\n" )
				outfile.write( f"Terminal?    {done}\n\n" )
				
			# update the custom class-variable created in ``__init__`` and used in ``render``
			self.last_sequence = (self.old_obs, action, reward)
			
			# gym-required return values (same as original)
			return obs, reward, done, info
			
		def render(self):
			""" Rewrite render method completely """
			# don't call ``super().render()`` here since we don't want to trigger that code
			print(f"{self.last_sequence[0]} -> {self.last_sequence[1]}\n\t= {self.last_sequence[1]}\n")
			

Data type conversion
---------------------

*Preface*

Alpyne follows the same rules as the AnyLogic Cloud's API defines. You can read more from here: https://cloud.anylogic.com/files/api-8.5.0/docs/index.html#7-data-conversion.

This section expands upon those rules, describing the nuances of a feature available in Alpyne.

*Introduction*

In most cases, values you set in data elements are type-checked against the defined constant; not abiding by the types set will cause errors to occur. For example, if an element's type is set to ``"DOUBLE"`` and you set the value to the string "hello", this will be rejected.

If you only ever use the template objects (accessible as attributes of the ``AlpyneClient`` object), the following will be irrelevant. 

For convenience, Alpyne also supports dynamic object creation. What this means is that the following two code blocks will initialize the model the same way:

::

	# Example 1
	app = AlpyneClient("...")
	
	config = app.configuration_template
	config.num_workers = 10
	config.arrival_rate = 3.14
	
	sim = app.create_reinforcement_learning(config)



::

	# Example 2
	app = AlpyneClient("...")
	
	config = Configuration(num_workers=10, arrival_rate=3.14)
	
	sim = app.create_reinforcement_learning(config)
	
In Example 1, the usage of the template will ensure the ``type`` key is set correctly. However, it can be cumbersome and reduce code legibility to pass in template objects when using model runs with other libraries (e.g., in custom gym environments). Example 2 removes the need to reference the parent application by allowing the Configuration to be created in-line. 

*Details*
The issue with example 2 above is that it creates type-ambiguity and might technically throw errors when passing that back to Java.

To clarify: Java has 4 types for whole numbers (byte, short, int, long) and 2 for floating point (float, double), whereas Python has one type for each category (int and float). While the type mapping is automatic from Java to Python (e.g., Java's ``long`` => Python's ``int``; Java's ``double`` => Python's ``float``), the ambiguity lies when passing from Python to Java. 

Alpyne supports these cases by having some leniency in the verification of types. The general rule is that Python will assume your model (in Java) is looking for the highest level of precision, which the underlying Alpyne app will reduce back to the appropriate type. 

In example 2 above, Python will set the type of ``num_workers`` to ``"LONG"`` and ``arrival_rate`` to ``"DOUBLE"``. Even if the model's Configuration defined the  types to be ``int`` and ``float`` (respectively), these will be accepted.