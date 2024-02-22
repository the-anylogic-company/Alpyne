import logging

from tabulate import tabulate

from alpyne.sim import AnyLogicSim

DIRECTION_LOOKUP = dict(
    e="EAST",
    s="SOUTH",
    w="WEST",
    n="NORTH",
    ne="NORTHEAST",
    nw="NORTHWEST",
    se="SOUTHEAST",
    sw="SOUTHWEST"
)

def print_board(status):
    """
    Prints a representation of the current board.

    The agent is expressed as a smiley face 's row/column is shown in the top
    """
    obs = status.observation
    board = [["■" if i == -1 else ("⌂" if i == 1 else " ") for i in row] for row in obs['cells']]
    board[obs['pos'][0]][obs['pos'][1]] = "☺"

    border = "- " * len(obs['cells'][0])
    body = "\n".join(" ".join(row) for row in board)
    print(f"{border}{status.observation['pos']}\n{body}\n{border}{str(status.stop)[0]}")

if __name__ == '__main__':
    # the seed determines the board configuration
    sim = AnyLogicSim(r"ModelExported\model.jar", engine_overrides=dict(seed=147))

    # predefine the configuration each run will use
    config = dict(numHoles=6, minStepsRequired=4, useMooreNeighbors=True, slipChance=0.0, throwOnInvalidActions=False)


    print("KEY:\n" + tabulate([["☺", "Player"], ["■", "Hole"], ["⌂", "Goal"]], headers=("symbol", "object"), stralign="center", tablefmt="fancy_grid"))
    print("Valid directions:", list(DIRECTION_LOOKUP.keys()))
    print("Board includes [row, column] and terminal status (T or F). Episodes will automatically reset.")
    print("Send keyboard interrupt or empty string to stop episodes.\n")
    while True:
        try:
            status = sim.reset(**config)
            print_board(status)

            while not status.stop:
                # ask for next move, pestering until a valid input is given
                direction_abbreviation = input("? ")
                if direction_abbreviation == "":
                    raise KeyboardInterrupt()
                while direction_abbreviation not in DIRECTION_LOOKUP:
                    direction_abbreviation = input("? ")
                direction = DIRECTION_LOOKUP[direction_abbreviation]

                status = sim.take_action({"dir": direction})
                print_board(status)

            print("\n")

        except KeyboardInterrupt:
            break