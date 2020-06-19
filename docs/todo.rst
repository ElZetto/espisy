#####
ToDo
#####

.. todo::

            **Bug**

            affects: :meth:`espisy.core.ESP.scan_network`

            When executing the loop, the request at IP x.x.x.255 raises an 
            `request.ConnectionError <https://2.python-requests.org/en/master/api/#requests.ConnectionError>`_ (External link)
            
            "address is invalid in this context".