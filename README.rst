========================
Django Check Constraints
========================

Django check constraints is a project that implements `check constraints`_ on 
models. The various check constraints implemented are:

  * Range Based Check Constraints
  * Value Based Check Constraints

These constraints are added at the database level during the creation of tables
through `syncdb` and at the model level by automagically adding validators to
the respective fields. The model validation works similar to how it works in 
trunk ie the `full_clean` method is called only on `ModelForm`'s save. For 
every other case, the user is responsible for calling the `full_clean` method.

The project was developed as a part of `Google Summer of Code 2007`_ but due 
to the lack of model validation could not make much progress then. But with 
model validation making it in django v1.2, the project has been resurrected. 
The idea for the project was given by `Kenneth Gonsalves`_ and was mentored 
by `Simon Blanchard`_.

.. _`check constraints`: http://en.wikipedia.org/wiki/Check_Constraint
.. _`Google Summer of Code 2007`: http://code.google.com/soc/2007/django/appinfo.html?csaid=63426CED5B1E571B
.. _`Kenneth Gonsalves`: http://lawgon.livejournal.com/
.. _`Simon Blanchard`: http://www.simonb.com/

---------
INSTALL
---------

* Patch your django code with the `django_check_constraints.diff` file::

     $ git apply django_check_constraints.diff

* Add the `check_constraints` app anywhere on your `PYTHONPATH` or just
  add it into your project directory and reference it in the `INSTALLED_APPS`.

* Run the check constraint test suite to figure if everything went well::

     $ python manage.py test check_constraints


-------
Usage
-------

* Check out http://code.google.com/p/django-check-constraints/wiki/Features
  for the features of django check constraints.
