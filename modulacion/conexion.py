from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable,AuthError
   
URI="bolt://localhost:7687"
AUTH=("neo4j","123456")


class Neo4jConnection :
     
    def __init__(self):
        self.driver=GraphDatabase.driver(URI,AUTH)

    def start_connection():
        try:
            with GraphDatabase.driver(URI,auth=AUTH) as driver :
                respuesta=driver.verify_authentication()
            
                #print("Conexion Establecida")   
                
            return driver
            
        except(ServiceUnavailable, AuthError) as e:
            print(f"Error al ejecutar al conectar a Neo4j: {e}")
        
        

    def close_connection(driver):
       if driver:
            driver.close()
            #print("Conexion Cerrada")

    def excute_querry(driver,querry):
       
        with driver.session(database="neo4j") as sesion:
        
            try:                
                result=sesion.run(querry)
                return result
            except Exception as e:
                print(f"Error al ejecutar la querry :{e}")
                return None

    
    def clearNeo4j(driver):
        with driver.session(database="neo4j") as session:
            clear="MATCH (n) OPTIONAL MATCH (n)-[r]-() DELETE n,r "
            session.run(clear)

    def topology(driver,querry):
       
        with driver.session(database="neo4j") as sesion:
        
            try:                
                result=sesion.run(querry)
                return result.data()
            except Exception as e:
                print(f"Error al ejecutar la querry :{e}")
                return None
        driver.close()
    