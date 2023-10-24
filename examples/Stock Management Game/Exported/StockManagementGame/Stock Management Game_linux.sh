#!/bin/sh
# 
# Run AnyLogic Experiment
# 
DIR_BACKUP_XJAL=$(pwd)
SCRIPT_DIR_XJAL=$(dirname "$0")
cd "$SCRIPT_DIR_XJAL"
chmod +x chromium/chromium-linux64/chrome

java -cp model.jar:lib/MarkupDescriptors.jar:lib/com.anylogic.engine.jar:lib/com.anylogic.engine.datautil.jar:lib/com.anylogic.engine.editorapi.jar:lib/com.anylogic.engine.generalization.jar:lib/com.anylogic.engine.sa.jar:lib/sa/com.anylogic.engine.sa.web.jar:lib/sa/executor-basic-8.3.jar:lib/sa/ioutil-8.3.jar:lib/sa/jackson/jackson-annotations-2.14.1.jar:lib/sa/jackson/jackson-core-2.14.1.jar:lib/sa/jackson/jackson-databind-2.14.1.jar:lib/sa/spark/javax.servlet-api-3.1.0.jar:lib/sa/spark/jetty-client-9.4.48.v20220622.jar:lib/sa/spark/jetty-continuation-9.4.48.v20220622.jar:lib/sa/spark/jetty-http-9.4.48.v20220622.jar:lib/sa/spark/jetty-io-9.4.48.v20220622.jar:lib/sa/spark/jetty-security-9.4.48.v20220622.jar:lib/sa/spark/jetty-server-9.4.48.v20220622.jar:lib/sa/spark/jetty-servlet-9.4.48.v20220622.jar:lib/sa/spark/jetty-servlets-9.4.48.v20220622.jar:lib/sa/spark/jetty-util-9.4.48.v20220622.jar:lib/sa/spark/jetty-webapp-9.4.48.v20220622.jar:lib/sa/spark/jetty-xml-9.4.48.v20220622.jar:lib/sa/spark/slf4j-api-1.7.25.jar:lib/sa/spark/spark-core-2.9.3.jar:lib/sa/spark/websocket-api-9.4.31.v20200723.jar:lib/sa/spark/websocket-client-9.4.31.v20200723.jar:lib/sa/spark/websocket-common-9.4.31.v20200723.jar:lib/sa/spark/websocket-server-9.4.31.v20200723.jar:lib/sa/spark/websocket-servlet-9.4.31.v20200723.jar:lib/sa/util-8.3.jar:lib/database/querydsl/querydsl-core-5.0.0.jar:lib/database/querydsl/querydsl-sql-5.0.0.jar:lib/database/querydsl/querydsl-sql-codegen-5.0.0.jar:lib/commons-lang3-3.9.jar:lib/commons-io-2.11.0.jar:lib/poi/commons-collections4-4.4.jar:lib/poi/dom4j-1.6.1.jar:lib/poi/poi-3.17.jar:lib/poi/poi-examples-3.17.jar:lib/poi/poi-excelant-3.17.jar:lib/poi/poi-ooxml-3.17.jar:lib/poi/poi-ooxml-schemas-3.17.jar:lib/poi/poi-scratchpad-5.2.1.jar:lib/poi/xmlbeans-2.6.0.jar:lib/com.anylogic.rl.data.jar:lib/com.anylogic.rl.connector.support.jar:lib/com.anylogic.rl.connector.bonsai.jar -Xmx512m stock_management_game1.RLExperiment $*

cd "$DIR_BACKUP_XJAL"
