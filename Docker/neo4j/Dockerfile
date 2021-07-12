FROM neo4j:4.1.1


COPY payload/apoc-4.1.0.0-all.jar /var/lib/neo4j/plugins/apoc-4.1.0.0-all.jar
COPY payload/neo4j-graph-data-science-1.4.0-* /var/lib/neo4j/plugins/

RUN echo "dbms.security.procedures.unrestricted=gds.*,apoc.*" >> conf/neo4j.conf
RUN echo "dbms.security.procedures.whitelist=apoc.*,gds.*" >> conf/neo4j.conf
RUN echo "dbms.jvm.additional=-Xss2M" >> conf/neo4j.conf
RUN echo "apoc.export.file.enabled=true" >> conf/apoc.conf
