var mongoose = require('mongoose');
var Schema = mongoose.Schema;
var bcrypt = require('bcrypt-nodejs');

mongoose.Promise = global.Promise;

//mongoose.connect(process.env.DB, { useNewUrlParser: true });
try {
    mongoose.connect( process.env.DB_URL, {useNewUrlParser: true, useUnifiedTopology: true}, () =>
        console.log("connected"));
}catch (error) {
    console.log("could not connect");
}
mongoose.set('useCreateIndex', true);

//game schema
var PlayerSeasonSchema = new Schema({
    playerId: Number,
    year: Number,
    G: Number,
    A: Number,
    P: Number,
    TOI: Number,
    CF: Number,
    CA: Number,
    FF: Number,
    FA: Number,
    PIM: Number,
    FOW: Number,
    FOL: Number,
    gamesPlayed: []
});

//return the model to server
module.exports = mongoose.model('PlayerSeasons', PlayerSeasonSchema);