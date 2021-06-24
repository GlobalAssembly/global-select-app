
const fs =require('fs')
const express = require('express')
var cors = require('cors')
const {spawn} = require('child_process');
const app = express()
app.use(cors())
const port = 3040

const pyScriptFile='global-select-admin-centroids.py'


// serving the static files
app.use('/resources', express.static('docs'))

// Add headers
app.use(function (req, res, next) {
    // Website you wish to allow to connect
    res.setHeader('Access-Control-Allow-Origin', '*');
    // Pass to next layer of middleware
    next();
});



// Endpoint to read the locations of the selected people from .txt file
app.get('/read', (req, res) => {
    fs.readFile('/home/developer/projects/global-select-app/results.txt','utf8',(err,data)=>{
        var nameArr = data.split('___');
        var new_array=[]
        for (let i = 0; i < nameArr.length-1; i++) {
            const element = nameArr[i];
            var el = element.split(",");
            new_array.push({lat:el[0],long:el[1],address:el[2],country:el[3]})    
        }
        res.send(new_array)
   })
})

//Reading  from the previous .csv file
app.get('/read-extended', (req, res) => {
    fs.readFile('/home/developer/projects/global-select-app/docs/global-ca-people-points.csv','utf8',(err,data)=>{
        var resp= data.split('region_name, region_max, region_count')
        res.send(resp)
    })    
})

app.listen(port, () => console.log(`Listening on port ${port}!`))
