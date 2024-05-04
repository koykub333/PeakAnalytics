var mongoose = require('mongoose');
var Schema = mongoose.Schema;
var bcrypt = require('bcrypt-nodejs');

mongoose.Promise = global.Promise;

//mongoose.connect(process.env.DB, { useNewUrlParser: true });
try {
    mongoose.connect( process.env.DB, {useNewUrlParser: true, useUnifiedTopology: true}, () =>
        console.log("connected"));
}catch (error) {
    console.log("could not connect");
}
mongoose.set('useCreateIndex', true);

//game schema
var PlayerSchema = new Schema({
    teamId: Number,
    playerId: Number,
    firstName: {},
    lastName: {},
    sweaterNumber: Number,
    positionCode: String,
    headshot: String
});

//return the model to server
module.exports = mongoose.model('Players', PlayerSchema);