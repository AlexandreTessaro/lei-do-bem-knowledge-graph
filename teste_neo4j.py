from neo4j import GraphDatabase

# URI examples: "neo4j://localhost", "neo4j+s://xxx.databases.neo4j.io"
URI = "neo4j://127.0.0.1:7687"
AUTH = ("neo4j", "a9OgI3u-ptaRuElG15HTW5Wf3b-wnyUs7DysPM1fiHw")

with GraphDatabase.driver(URI, auth=AUTH) as driver:
    driver.verify_connectivity()