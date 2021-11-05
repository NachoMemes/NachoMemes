const corde = require("corde");
const { spawnSync } = require("child_process");

corde.group("main commands", () => {
  corde.test("help should return help", () => {
    corde
      .expect("help")
      .toMessageContentContains(
        "A bot to generate custom memes using pre-loaded templates."
      );
  });
});
