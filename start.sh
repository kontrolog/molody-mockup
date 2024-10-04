#!/bin/sh
#gunicorn main:app --bind 0.0.0.0:10000

#!/bin/bash
gunicorn main:app -b 0.0.0.0:$PORT