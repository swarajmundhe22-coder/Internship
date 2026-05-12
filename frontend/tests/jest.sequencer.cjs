const Sequencer = require("@jest/test-sequencer").default;

class StablePathSequencer extends Sequencer {
  sort(tests) {
    return [...tests].sort((a, b) => a.path.localeCompare(b.path));
  }
}

module.exports = StablePathSequencer;
