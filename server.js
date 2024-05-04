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
        Players.find( function(err,players){
            if(err){
                res.send(err);
            } else {
                res.json(players);
            }
        });
    })
    .post(authJwtController.isAuthenticated, (req, res) =>{

    })
    .put(authJwtController.isAuthenticated, (req,res) => {

    })
    .delete(authJwtController.isAuthenticated, (req,res) =>{

    })
    .all( (req,res) => {
        // Any other HTTP Method
        // Returns a message stating that the HTTP method is unsupported.
        res.status(405).send({ message: 'HTTP method not supported.' });        
    });

router.route('/players/:playerId')
    .get( (req,res) => {
        console.log("GET PLAYERS request received.");
        const { id } = req.params;
        Players.findOne({ playerId: id }, function(err,player){
            if(err){
                res.send(err);
            } else {
                res.json(player);
            }
        });
    })
    .post(authJwtController.isAuthenticated, (req, res) =>{

    })
    .put(authJwtController.isAuthenticated, (req,res) => {

    })
    .delete(authJwtController.isAuthenticated, (req,res) =>{

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
        Games.find( function(err,games){
            if(err){
                res.send(err);
            } else {
                res.json(games);
            }
        });
    })
    .post(authJwtController.isAuthenticated, (req, res) =>{

    })
    .put(authJwtController.isAuthenticated, (req,res) => {

    })
    .delete(authJwtController.isAuthenticated, (req,res) =>{

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

    })
    .put(authJwtController.isAuthenticated, (req,res) => {

    })
    .delete(authJwtController.isAuthenticated, (req,res) =>{

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

    })
    .put(authJwtController.isAuthenticated, (req,res) => {

    })
    .delete(authJwtController.isAuthenticated, (req,res) =>{

    })
    .all( (req,res) => {
        // Any other HTTP Method
        // Returns a message stating that the HTTP method is unsupported.
        res.status(405).send({ message: 'HTTP method not supported.' });        
    });

router.route('/playerSeasons/:playerId')
    .get( (req,res) => {
        console.log("GET PLAYER SEASONS request received.");
        const{ id } = req.params;

        PlayerSeasons.find( { playerId: id }, function(err,playerSeasons){
            if(err){
                res.send(err);
            } else {
                res.json(playerSeasons);
            }
        });
    })
    .post(authJwtController.isAuthenticated, (req, res) =>{

    })
    .put(authJwtController.isAuthenticated, (req,res) => {

    })
    .delete(authJwtController.isAuthenticated, (req,res) =>{

    })
    .all( (req,res) => {
        // Any other HTTP Method
        // Returns a message stating that the HTTP method is unsupported.
        res.status(405).send({ message: 'HTTP method not supported.' });        
    });
