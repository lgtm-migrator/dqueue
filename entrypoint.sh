echo "APP_MODE: ${APP_MODE:=api}"

if [ ${APP_MODE:?} == "api" ]; then
    #gunicorn --workers 8 dqueue.api:app -b 0.0.0.0:8000 --timeout 600 --log-level DEBUG 2>&1 | cut -c1-500
    #gunicorn --workers 8 dqueue.api:app -b 0.0.0.0:8000 --timeout 600 --log-level DEBUG 2>&1 
    if [ "${DQUEUE_SILENT:-yes}" == "yes" ]; then
        gunicorn --workers 8 dqueue.api:app -b 0.0.0.0:8000 --log-level ${DQUEUE_LOG_LEVEL:-WARNING} --timeout 600 2>&1 | grep -v DEBUG | grep -v INFO | cut -c1-500
    else
        gunicorn --workers 8 dqueue.api:app -b 0.0.0.0:8000 --log-level DEBUG --timeout 600 2>&1
    fi
elif [ ${APP_MODE:?} == "guardian" ]; then
    while true; do
        dqueue guardian -w 30
        sleep 1
    done    
elif [ ${APP_MODE:?} == "callbackworker" ]; then
    while true; do
        dqueue server callback run-next-callback
        sleep 5
    done
else
    echo 'unknown APP_MODE! can be "api" or "guardian"'
    exit 1
fi

