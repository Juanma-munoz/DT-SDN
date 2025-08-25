const express = require('express');
const neo4j = require('neo4j-driver');
const cors = require('cors');

const port = 3000;
const app = express();

app.use(cors());

// Inicializa el driver de Neo4j
const driver = neo4j.driver('neo4j://localhost', neo4j.auth.basic('neo4j', '123456'));

// Endpoint para obtener switches
app.get('/switches', async (req, res) => {
    const session = driver.session();
    try {
        const result = await session.run('MATCH (s:Switch) RETURN s');
        const switches = result.records.map(record => ({
            switches: record.get('s').properties,
        }));
        
    
        res.json(switches);
    } catch (error) {
        console.error('Error fetching switches:', error);
        res.status(500).send('Error fetching switches');
    } finally {
        session.close(); // Cierra la sesión después de la solicitud
    }
});

// Endpoint para obtener hosts
app.get('/hosts', async (req, res) => {
    const session = driver.session();
    try {
        const result = await session.run('MATCH (h:Host) RETURN h');
        const hosts = result.records.map(record => ({
            hosts: record.get('h').properties,
        }));




        
        console.log(hosts);
        res.json(hosts);
    } catch (error) {
        console.error('Error fetching hosts:', error);
        res.status(500).send('Error fetching hosts');
    } finally {
        session.close(); // Cierra la sesión después de la solicitud
    }
});




// Endpoint para obtener links
app.get('/links', async (req, res) => {
    const session = driver.session();
    try {
        const result = await session.run('MATCH p=()-[r:Link]->() RETURN p');

        const links = result.records.map(record => {
            const path = record.get('p'); // Obtiene el camino completo
            return path.segments.map(segment => ({
                relationship: segment.relationship.properties, // Propiedades de la relación
            }));
        });
        
        // Imprime los datos procesados
        console.log(links);
        res.json(links)
            
        
    } catch (error) {
        console.error('Error fetching hosts:', error);
        res.status(500).send('Error fetching hosts');
    } finally {
        session.close(); // Cierra la sesión después de la solicitud
    }
});

// Endpoint para obtener la pérdida de paquetes del enlace entre dos switches
app.get('/metrics', async (req, res) => {
    
    const { origen, destino } = req.query; // Recibe los parámetros desde la URL
    const session = driver.session();

    try {
        if (!origen || !destino) {
            return res.status(400).json({ error: "Faltan parámetros origen y destino" });
        }
        console.log("El orgien es",origen,"El destino es",destino)
        const result = await session.run(
            `MATCH (:Switch {switch_dpid: $origen})-[r:Link]->(:Switch {switch_dpid: $destino}) 
            RETURN r.perdidas , r.delay, r.throughput`,
            { origen: Number(origen), destino: Number(destino) },
        
        );

        if (result.records.length > 0) {
            res.json({ origen, destino, 
                perdidas: result.records[0].get('r.perdidas'),
                delay: result.records[0].get('r.delay'),
                throughput:result.records[0].get('r.throughput') });
        } else {
            res.status(404).json({ error: "Enlace no encontrado" });
            
        }
    } catch (error) {
        console.error('Error obteniendo pérdida de paquetes:', error);
        res.status(500).send('Error obteniendo pérdida de paquetes');
    } finally {
        await session.close();
    }
});

// Cierra el driver de Neo4j al salir del proceso
process.on('exit', () => {
    driver.close();
    console.log('Neo4j driver closed');
});

// Inicia el servidor
app.listen(port, () => console.log(`Server running on http://localhost:${port}`));
