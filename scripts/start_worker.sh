#!/bin/bash
celery -A services.tasks worker -B -l info
