/*
Koy Kubasta
Peak Hockey Analytics
*/

var express = require('express');
var bodyParser = require('body-parser');
var passport = require('passport');
var authJwtController = require('./auth_jwt');
var jwt = require('jsonwebtoken');
var cors = require('cors');
var User = require('./Users');
var Games = require('./Games');
var Players = require('./Players');
var PlayerSeasons = require('./PlayerSeasons');
const spawn = require("child_process").spawn;


var app = express();
app.use(cors());
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: false }));

app.use(passport.initialize());

var router = express.Router();

router.post('/signup', function(req, res) {
    if (!req.body.username || !req.body.password) {
        res.json({success: false, msg: 'Please include both username and password to signup.'})
    } else {
        var user = new User();
        user.name = req.body.name;
        user.username = req.body.username;
        user.password = req.body.password;

        user.save(function(err){
            if (err) {
                if (err.code == 11000)
                    return res.json({ success: false, message: 'A user with that username already exists.'});
                else
                    return res.json(err);
            }

            res.json({success: true, msg: 'Successfully created new user.'})
        });
    }
});

router.post('/signin', function (req, res) {
    var userNew = new User();
    userNew.username = req.body.username;
    userNew.password = req.body.password;

    User.findOne({ username: userNew.username }).select('name username password').exec(function(err, user) {
        if (err) {
            res.send(err);
        }

        user.comparePassword(userNew.password, function(isMatch) {
            if (isMatch) {
                var userToken = { id: user.id, username: user.username };
                var token = jwt.sign(userToken, process.env.SECRET_KEY);
                res.json ({success: true, token: 'JWT ' + token});
            }
            else {
                res.status(401).send({success: false, msg: 'Authentication failed.'});
            }
        })
    })
});


/******************************************************** */
/*                          PLAYERS                       */
/******************************************************** */
router.route('/players')
    .get( (req,res) => {
        console.log("GET PLAYERS request received.");
        Players.find().then(players => {
                res.json(players);
        });
    })
    .post(authJwtController.isAuthenticated, (req, res) =>{
        // Update Players
        console.log("POST PLAYERS request received.");
        if(!req.query.gameId) {
            res.status(400).send({ message: "Requires a game ID to update players by." });
        } else {
            console.log(req.query.gameId);
            spawn('python', [".\\pyscripts\\dbhandler.py", "updatePlayers", req.query.gameId]);
            res.status(200).send({ message: "Update request recieved. Process may take a few minutes to update results to server." });
        }
    })
    .delete(authJwtController.isAuthenticated, (req,res) =>{
        console.log("DELETE PLAYER request received.");
        if(!req.query.playerId) {
            res.status(400).send({ message: "Please specify a player to delete." });
        } else {
            Players.deleteOne( { playerId: req.query.playerId }, function(err){
                if (err) {
                    console.log("Failed to delete Player.");
                    res.json(err);
                } else {
                    console.log("Player deleted.");
                    res.json({success: true, msg: "Successfully deleted player."});
                }
            });
        }
    })
    .all( (req,res) => {
        // Any other HTTP Method
        // Returns a message stating that the HTTP method is unsupported.
        res.status(405).send({ message: 'HTTP method not supported.' });        
    });

router.route('/players/:playerId')
    .get( (req,res) => {
        console.log("GET PLAYERS request received.");
        const { playerId } = req.params;
        Players.findOne({ playerId: playerId }, function(err,player){
            if(err){
                res.send(err);
            } else {
                console.log(player);
                res.json(player);
            }
        });
    })
    .delete(authJwtController.isAuthenticated, (req,res) =>{
        const { playerId } = req.params;
        Players.deleteOne({ playerId: playerId }, function(err){
            if (err) {
                console.log("Failed to delete player.");
                res.json(err);
            } else {
                console.log("Player deleted.");
                res.json({success: true, msg: "Successfully deleted player."});
            }
        });
    })
    .all( (req,res) => {
        // Any other HTTP Method
        // Returns a message stating that the HTTP method is unsupported.
        res.status(405).send({ message: 'HTTP method not supported.' });        
    });


/******************************************************** */
/*                          GAMES                         */
/******************************************************** */
router.route('/games')
    .get( (req,res) => {
        console.log("GET GAMES request received.");
        Games.find().then( games => {
            res.json(games);
        });
    })
    .post(authJwtController.isAuthenticated, (req, res) =>{
        console.log("POST GAME request recieved.");
        if(!req.query.gameId){
            console.log("Update failed: Missing game specification.");
            res.json({success: false, msg: "Please specify a game to update."});
        } else {
            spawn('python', [".\\pyscripts\\dbhandler.py", "updateGame", req.query.gameId]);
            res.json({success: true, msg: "Successfully updating game. Process may take a few minutes to complete."});
        }
    })
    .delete(authJwtController.isAuthenticated, (req,res) =>{
        console.log("DELETE GAME request received.");
        if (!req.query.gameId) {
            console.log("DELETE failed: Missing game specification.");
            res.json({success: false, msg: "Please specify a game to delete."});
        } else {
            Games.deleteOne({ id : req.query.gameId}, function(err){
                if (err) {
                    console.log("Failed to delete game.");
                    res.json(err);
                } else {
                    console.log("Game deleted.");
                    res.json({success: true, msg: "Successfully deleted game."});
                }
            });
        }
    })
    .all( (req,res) => {
        // Any other HTTP Method
        // Returns a message stating that the HTTP method is unsupported.
        res.status(405).send({ message: 'HTTP method not supported.' });        
    })

router.route('/games/:gameId')
    .get( (req,res) => {
        console.log("GET GAMES request received.");
        const{ gameId } = req.params;

        Games.findOne({ id: gameId }, function(err,game){
            if(err){
                res.send(err);
            } else {
                res.json(game);
            }
        });
    })
    .post(authJwtController.isAuthenticated, (req, res) =>{
        console.log("POST GAMES request received.");
        const { gameId } = req.params;

        spawn('python', [".\\pyscripts\\dbhandler.py", "updateGame", gameId]);
        res.json({success: true, msg: "Successfully updating game. Process may take a few minutes to complete."});   
    })
    .delete(authJwtController.isAuthenticated, (req,res) =>{
        console.log("DELETE GAME request received.");
        const { gameId } = req.params;

        Games.deleteOne({ id: gameId }, function(err){
            if (err){
                console.log("Failed to delete game.");
                res.json(err);
            } else {
                console.log("Game deleted.");
                res.json({success: true, msg: "Successfully deleted game."});
            }
        });
    })
    .all( (req,res) => {
        // Any other HTTP Method
        // Returns a message stating that the HTTP method is unsupported.
        res.status(405).send({ message: 'HTTP method not supported.' });        
    });


/******************************************************** */
/*                      PLAYER SEASONS                    */
/******************************************************** */
router.route('/playerSeasons')
    .get( (req,res) => {
        console.log("GET PLAYER SEASONS request received.");
        PlayerSeasons.find( function(err,playerSeasons){
            if(err){
                res.send(err);
            } else {
                res.json(playerSeasons);
            }
        });
    })
    .post(authJwtController.isAuthenticated, (req, res) =>{
        console.log("POST PLAYER SEASONS request received.");
        if (!req.query.year){
            console.log("Update player seasons failed: Missing year specification.");
            res.status(400).send({success: false, msg: "Please specify year."});
        } else {
            spawn('python', [".\\pyscripts\\dbhandler.py", "updateSeason", req.query.year]);
            res.json({success: true, msg: "Successfully updating player seasons. May take a long time to process."});
        }
    })
    .all( (req,res) => {
        // Any other HTTP Method
        // Returns a message stating that the HTTP method is unsupported.
        res.status(405).send({ message: 'HTTP method not supported.' });        
    });

router.route('/playerSeasons/:playerId')
    .get( (req,res) => {
        console.log("GET PLAYER SEASONS request received.");
        const{ playerId } = req.params;

        PlayerSeasons.find( { playerId: playerId }, function(err,playerSeasons){
            if(err){
                res.send(err);
            } else {
                res.json(playerSeasons);
            }
        });
    })
    .delete(authJwtController.isAuthenticated, (req,res) =>{
        console.log("DELETE PLAYER SEASON request received.");
        const { playerId } = req.params;
        if (!req.query.year) {
            console.log("Delete failed: Year not specified.");
            res.status(400).send({message: "Please specify a year."});
        } else {
            PlayerSeasons.deleteOne({playerId: playerId, year: req.query.year}, function(err){
                if (err){
                    console.log("Failed to delete Player Season.");
                    res.json(err);
                } else {
                    console.log("Player Season deleted.");
                    res.json({success: true, msg: "Successfully deleted player season."});
                }
            });
        }
    })
    .all( (req,res) => {
        // Any other HTTP Method
        // Returns a message stating that the HTTP method is unsupported.
        res.status(405).send({ message: 'HTTP method not supported.' });        
    });


app.use('/', router);
app.listen(process.env.PORT || 8080);
module.exports = app;