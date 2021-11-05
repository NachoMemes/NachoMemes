module.exports = {
  botTestId: "630996450083340289",
  guildId: "557224886125461521",
  channelId: "904867360031277056",
  botPrefix: "!",
  testMatches: ["./integration-test/**"],
};

function readEnvVar(name) {
  let value = process.env[name];
  if (value == null || value.trim() === "") {
    throw new Error(`Environment variable ${name} is empty!`);
  }
  return value;
}

let cordeToken = readEnvVar("CORDE_BOT_TOKEN");
let botToken = readEnvVar("TEST_BOT_TOKEN");
module.exports.cordeBotToken = cordeToken;
module.exports.botToken = botToken;
