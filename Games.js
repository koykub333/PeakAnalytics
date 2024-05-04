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
var GameSchema = new Schema({
    id: Number,
    season: Number,
    gameType: Number,
    limitedScoring: Boolean,
    gameDate: String,
    venue: {},
    venueLocation: {},
    startTimeUTC: String,
    easternUTCOffset: String,
    venueUTCOffset: String,
    tvBroadcasts: [],
    gameState: String,
    gameScheduleState: String,
    periodDescriptor: {},
    awayTeam: {},
    homeTeam: {},
    shootoutInUse: Boolean,
    otInUse: Boolean,
    clock: {},
    displayePeriod: Number,
    maxPeriods: Number,
    gameOutcome: {},
    plays: [],
    rosterSpots: [],
    gameVideo: {},
    regPeriods: Number,
    summary: {},
    playerGames: {}
});

//return the model to server
module.exports = mongoose.model('Games', GameSchema);