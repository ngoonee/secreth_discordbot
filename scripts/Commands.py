from main import games, log
import asyncio

from discord.abc import PrivateChannel
import discord
import random
from random import randrange
from time import sleep, time, monotonic
import json

from Board import Board
from Constants import players
from Game import Game
from Player import Player

from Config import ADMIN, PREFIX

symbols = [
    u"\u25FB\uFE0F" + ' Empty field without special power',
    ':x: Field covered with a card',  # X
    u"\U0001F52E" + ' Presidential Power: Policy Peek',  # crystal
    u"\U0001F50E" + ' Presidential Power: Investigate Loyalty',  # inspection glass
    u"\U0001F5E1" + ' Presidential Power: Execution',  # knife
    u"\U0001F454" + ' Presidential Power: Call Special Election',  # tie
    u"\U0001F54A" + ' Liberals win',  # dove
    u"\u2620" + ' Fascists win'  # skull
]

embed_color = 10365218

def generate_embed(text, title):
    return discord.Embed(
        title=title if title else "Secret Hitler",
        type="rich",
        description=text,
        color=embed_color
    )

async def command_symbols(bot, msg, args):
    """Shows you all possible symbols of the board."""
    symbol_text = ""
    for i in symbols:
        symbol_text += i + "\n\n"
    await msg.channel.send(embed=generate_embed(symbol_text, "The following symbols can appear on the board:"))


async def command_board(bot, msg, args):
    """Prints the current board with fascist and liberal tracks, presidential order, and election counter."""
    cid = msg.channel.id
    if cid in games.keys():
        if games[cid].board is not None:
            await msg.channel.send(games[cid].board.print_board())
        else:
            await msg.channel.send("There is no running game in that chat. Please start the game with sh?startgame")
    else:
        await msg.channel.send("There is no game in that chat. Create a new game with sh?newgame")


async def command_start(bot, msg, args):
    """Gives you a short piece of information about Secret Hitler."""
    await msg.channel.send(
                     embed=generate_embed("*\"Secret Hitler is a social deduction game for 5-10 people about finding and stopping the Secret Hitler."+
                     " The majority of players are liberals. If they can learn to trust each other, they have enough "+
                     "votes to control the table and win the game. But some players are fascists. They will say whatever "+
                     "it takes to get elected, enact their agenda, and blame others for the fallout. The liberals must "+
                     "work together to discover the truth before the fascists install their cold-blooded leader and win "+
                     "the game.\"*\n\nType **sh?newgame** to create a game!", "Introduction"))
    await command_help(bot, msg, None)


async def command_rules(bot, msg, args):
    """Sends a link to the official Secret Hitler rules."""
    await msg.channel.send(embed=discord.Embed(title="Read the official Secret Hitler rules", description="http://www.secrethitler.com/assets/Secret_Hitler_Rules.pdf"))


# pings the bot
async def command_ping(bot, msg, args):
    """Pings the bot to check latency."""
    t1 = time()
    pong_msg = await msg.channel.send(':ping_pong: Pong')
    t2 = time()

    diff = round((t2 - t1) * 1000, 2)

    await pong_msg.edit(content=':ping_pong: Pong **{} ms**'.format(diff))


async def command_invite(bot, msg, args):
    """Sends a link to add the bot to another server."""
    em = discord.Embed(type="rich", title="Invite Secret Hitler Bot to a Server", description="https://discordapp.com/api/oauth2/authorize?client_id=702048291780558870&permissions=67631168&scope=bot", color=embed_color)
    await msg.channel.send(embed=em)


# prints statistics, only ADMIN
async def command_stats(bot, msg, args):
    """(ADMIN) Sends statistics about the bot."""
    cid = msg.author.id
    if cid == ADMIN:
        with open("stats.json", 'r') as f:
            stats = json.load(f)
        stattext = "**Liberal Wins (policies)** - " + str(stats.get("libwin_policies")) + "\n" + \
                    "**Liberal Wins (killed Hitler)** - " + str(stats.get("libwin_kill")) + "\n" + \
                    "**Fascist Wins (policies)** - " + str(stats.get("fascwin_policies")) + "\n" + \
                    "**Fascist Wins (Hitler chancellor)** - " + str(stats.get("fascwin_hitler")) + "\n" + \
                    "**Games cancelled** - " + str(stats.get("cancelled")) + "\n\n" + \
                    "**Total amount of groups** - " + str(len(stats.get("groups"))) + "\n" + \
                    "**Games running right now** - " + str(len(games))
        await msg.author.send(embed=generate_embed(stattext, "Statistics"))
        await msg.channel.send("Sent to DMs!")
    else:
        await msg.channel.send("You must be an admin to use this command.")


# help page
async def command_help(bot, msg, args):
    """Gives you information about the available commands."""
    cid = msg.author.id
    help_text = ""
    for name, func in sorted(globals().items()):
        if callable(func) and func.__module__ == __name__ and name.startswith('command_'):
            if func.__doc__.startswith("(ADMIN)"):
                if cid == ADMIN:
                    help_text += ("**" + PREFIX + name[8:] + "** - " + func.__doc__ + "\n")
            else:
                help_text += ("**" + PREFIX + name[8:] + "** - " + func.__doc__ + "\n")
    await msg.channel.send(embed=generate_embed(help_text, "The following commands are available:"))


async def command_about(bot, msg, args):
    """Information about the bot's authors and licensing."""
    await msg.channel.send(embed=generate_embed("This bot was originally developed for the chat client Telegram by Julian Schrittwieser.\n\nThis version has been adapted to Discord by James Shiffer, and uses the library discord.py. dszryan and Ng Oon-Ee updated it to discord.py 1.3.2.\nView the source code here: https://github.com/ngoonee/secreth_telegrambot/tree/discord\n\nCopyright and license Secret Hitler (© 2016 GOAT, WOLF, & CABBAGE) is designed by Max Temkin (Cards Against Humanity, Humans vs. Zombies) Mike Boxleiter (Solipskier, TouchTone), Tommy Maranges (Philosophy Bro) and illustrated by Mackenzie Schubert (Letter Tycoon, Penny Press). Secret Hitler is licensed under Creative Commons BY-NC-SA 4.0 and so is this bot.", "About Secret Hitler Bot"))


# shutdown, only ADMIN
async def command_shutdown(bot, msg, args):
    """(ADMIN) Shuts down the bot."""
    cid = msg.author.id
    if cid == ADMIN:
        await msg.channel.send('Shutting down...')
        exit(0)
    else:
        await msg.channel.send("You must be an admin to use this command.")

# broadcast message to all groups, only ADMIN
async def command_broadcast(bot, msg, args):
    """(ADMIN) Broadcasts a message to all servers."""
    cid = msg.author.id
    if cid == ADMIN:
        with open("stats.json", 'r') as f:
            stats = json.load(f)

        toremove = []
        async for i in bot.guilds:
            await i.default_channel.send(' '.join(args))
            log.info("message sent to group " + str(i))
        for i in toremove:
            stats.get("groups").remove(i)
        with open("stats.json", 'w') as f:
            json.dump(stats, f)
        await msg.author.send('Messages sent!')

async def command_newgame(bot, msg, args):
    """Creates a new game."""
    global game
    cid = msg.channel.id

    # If this is not a DM
    if not isinstance(msg.channel, PrivateChannel):
        if cid not in games.keys():
            games[cid] = Game(msg.channel, msg.author.id)
            with open("stats.json", 'r') as f:
                stats = json.load(f)
            if cid not in stats.get("groups"):
                stats.get("groups").append(cid)
                with open("stats.json", 'w') as f:
                    json.dump(stats, f)
            await msg.channel.send(
                             "New game created! Each player has to sh?join the game.\nThe initiator of this game (or the admin) can sh?join too and type sh?startgame when everyone has joined the game!")
        else:
            await msg.channel.send("There is currently a game running. If you want to end it please type sh?cancelgame!")
    else:
        await msg.author.send("You have to add me to a group first and type sh?newgame there!")


async def command_join(bot, msg, args):
    """Joins an existing game."""
    group_name = msg.guild.name if msg.guild else '[no name]'
    cid = msg.channel.id
    if not isinstance(msg.channel, PrivateChannel):
        if cid in games.keys():
            game = games[cid]
            uid = msg.author.id
            fname = msg.author.display_name
            if game.board is None:
                if uid not in game.playerlist:
                    if len(game.playerlist) < 10:
                        player = Player(fname, msg.author)
                        try:
                            await msg.author.send(
                                             "You joined a game in %s. I will soon tell you your secret role." % group_name)
                            game.add_player(uid, player)
                            if len(game.playerlist) > 4:
                                await game.channel.send(
                                                 fname + " has joined the game. Type sh?startgame if this was the last player and you want to start with %d players!" % len(
                                                     game.playerlist))
                            else:
                                if len(game.playerlist) == 1:
                                    await game.channel.send(
                                                     "%s has joined the game. There is currently 1 player in the game and you need 5-10 players." % (
                                                         fname))
                                else:
                                    await game.channel.send(
                                                     "%s has joined the game. There are currently %d players in the game and you need 5-10 players." % (
                                                         fname, len(game.playerlist)))
                        except Exception as e:
                            await game.channel.send(
                                             fname + ", I can\'t send you a DM. Please try sending sh?join again.")
                    else:
                        await game.channel.send(
                                         "You have reached the maximum amount of players. Please start the game with sh?startgame!")
                else:
                    await game.channel.send("You already joined the game, %s!" % fname)
            else:
                await msg.channel.send("The game has started. Please wait for the next game!")
        else:
            await msg.channel.send("There is no game in this chat. Create a new game with sh?newgame")
    else:
        await msg.channel.send("You have to add me to a group first and type sh?newgame there!")


async def command_startgame(bot, msg, args):
    """Starts an existing game once all players have joined."""
    log.info('command_startgame called')
    cid = msg.channel.id
    group_name = msg.guild.name
    if cid in games.keys():
        game = games[cid]
        status = msg.author.permissions_in(msg.channel)
        if game.board is None:
            if msg.author.id == game.initiator or status.administrator:
                player_number = len(game.playerlist)
                if player_number > 4:
                    # Tell people their roles and such
                    await inform_players(bot, game, player_number)
                    await inform_fascists(bot, game, player_number)
                    game.board = Board(player_number, game)
                    game.shuffle_player_sequence()
                    game.board.state.player_counter = 0
                    await game.channel.send(game.board.print_board())
                    # bot.send_message(ADMIN, "Game of Secret Hitler started in group %s (%d)" % (group_name, cid))
                    await start_round(bot, game)
                else:
                    await game.channel.send("There are not enough players (min. 5, max. 10). Join the game with sh?join")
            else:
                await game.channel.send("Only the initiator of the game or a group admin can start the game with sh?startgame")
        else:
            await msg.channel.send("The game is already running!")
    else:
        await msg.channel.send("There is no game in this chat. Create a new game with sh?newgame")


async def command_cancelgame(bot, msg, args):
    """Cancels an existing game. All game data will be lost!"""
    cid = msg.channel.id
    if cid in games.keys():
        game = games[cid]
        status = msg.author.permissions_in(msg.channel)
        if msg.author.id == game.initiator or status.administrator:
            await end_game(bot, game, 99)
        else:
            await msg.channel.send("Only the initiator of the game or a group admin can cancel the game with sh?cancelgame")
    else:
        await msg.channel.send("There is no game in this chat. Create a new game with sh?newgame")


##
#
# Beginning of round
#
##

async def start_round(bot, game):
    log.info('start_round called')
    if game.board.state.chosen_president is None:
        game.board.state.nominated_president = game.player_sequence[game.board.state.player_counter]
    else:
        game.board.state.nominated_president = game.board.state.chosen_president
        game.board.state.chosen_president = None
    await game.channel.send(
                     "The next presidential canditate is %s.\n%s, please nominate a Chancellor in our private chat!" % (
                         game.board.state.nominated_president.name, game.board.state.nominated_president.name))
    await choose_chancellor(bot, game)
    # --> nominate_chosen_chancellor --> vote --> handle_voting --> count_votes --> voting_aftermath --> draw_policies
    # --> choose_policy --> pass_two_policies --> choose_policy --> enact_policy --> start_round


async def choose_chancellor(bot, game):
    log.info('choose_chancellor called')
    pres_uid = 0
    chan_uid = 0
    btns = []
    if game.board.state.president is not None:
        pres_uid = game.board.state.president.user.id
    if game.board.state.chancellor is not None:
        chan_uid = game.board.state.chancellor.user.id
    log.info('currently president: {} and chancellor: {}'.format(game.board.state.president, game.board.state.chancellor))
    for uid in game.playerlist:
        # If there are only five players left in the
        # game, only the last elected Chancellor is
        # ineligible to be Chancellor Candidate; the
        # last President may be nominated.

        # This is intended to kill off AFK players, but effectively kills all games since the last_input is never reset...
        #if monotonic() > game.playerlist[uid].last_input + 20:
            #game.playerlist[uid].is_dead = True
        if len(game.player_sequence) > 5:
            if uid != game.board.state.nominated_president.user.id and game.playerlist[
                uid].is_dead == False and uid != pres_uid and uid != chan_uid:
                name = game.playerlist[uid].name
                btns.append({'name': name, 'uid': uid})
        else:
            if uid != game.board.state.nominated_president.user.id and game.playerlist[
                uid].is_dead == False and uid != chan_uid:
                name = game.playerlist[uid].name
                btns.append({'name': name, 'uid': uid})

    await game.board.state.nominated_president.user.send(game.board.print_board())
    await game.board.state.nominated_president.user.send('Please nominate your chancellor with sh?chan <id>!\nYour choices are:\n{}\n\nYou have 30 seconds.'
                                                         .format(
                                                             "\n".join(
                                                                 "["+ str(i+1) +"] " + p['name'] for i, p in enumerate(btns)
                                                                 )
                                                         )
    )

    def check_chancellor(msg):
        if not msg.author==game.board.state.nominated_president.user:
            return False
        validation = validate_message(msg)
        if not validation:
            return False
        cmd, arg = validation
        if not cmd == "chan":
            return False
        try:
            if not int(arg) > 0 or not int(arg) <= len(btns):
                return False
        except Exception:
            return False
        return True

    # Pick a random chancellor if they don't pick within 30 seconds
    try:
        msg = await bot.wait_for('message', check=check_chancellor, timeout=game.timeout)
        cmd, arg = validate_message(msg)
        chan_num = int(arg)
    except asyncio.TimeoutError:
        log.info('choose_chancellor timed out - random chancellor chosen')
        chan_num = random.choice([i for i, p in enumerate(btns)])
    await nominate_chosen_chancellor(bot,
                                     game,
                                     btns[chan_num-1]['uid'] if chan_num else random.choice(list(game.playerlist.keys()))
    )


async def nominate_chosen_chancellor(bot, game, chosen_uid):
    log.info('nominate_chosen_chancellor called')
    try:
        #game = games[cid]
        game.board.state.nominated_chancellor = game.playerlist[chosen_uid]
        log.info("President %s (%d) nominated %s (%d)" % (
            game.board.state.nominated_president.name, game.board.state.nominated_president.user.id,
            game.board.state.nominated_chancellor.name, game.board.state.nominated_chancellor.user.id))
        # bot.send_message("You nominated %s as Chancellor!" % game.board.state.nominated_chancellor.name, callback.from_user.id, callback.message.message_id)
        await game.channel.send(
                         "President %s nominated %s as Chancellor. Please vote now!" % (
                             game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name))
        await vote(bot, game)
    except AttributeError as e:
        log.error("nominate_chosen_chancellor: Game or board should not be None!")
    except Exception as e:
        log.error("Unknown error: " + str(e))


async def vote(bot, game):
    log.info('vote called')
    voted_msg = await game.channel.send(embed=discord.Embed(title="Voted:", description="*Nobody has voted*"))
    for uid in game.playerlist:
        log.info('voting instructions sent to {}'.format(game.playerlist[uid].user.name))
        # This is intended to kill off AFK players, but effectively kills all games since the last_input is never reset...
        #if monotonic() > game.playerlist[uid].last_input + 20:
            #game.playerlist[uid].is_dead = True
        if not game.playerlist[uid].is_dead:
            if game.playerlist[uid] is not game.board.state.nominated_president:
                # the nominated president already got the board before nominating a chancellor
                await game.playerlist[uid].user.send(game.board.print_board())
            await game.playerlist[uid].user.send(
                             "Do you want to elect President %s and Chancellor %s? Say sh?ja or sh?nein to continue. You have 30 seconds." % (
                                 game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name))
    while True:
        def check_vote(msg):
            validation = validate_message(msg)
            if not validation:
                return False
            cmd, _ = validation
            if cmd in ("ja", "nein"):
                return True
            else:
                return False
        try:
            msg = await bot.wait_for('message', check=check_vote, timeout=game.timeout)
            cmd, _ = validate_message(msg)
            vote = True if cmd == "ja" else False
            uid = msg.author.id
        except asyncio.TimeoutError:
            log.info('timeout while waiting for player votes, {} remaining'.format(
                len(game.player_sequence)- len(game.board.state.last_votes))
            )
            continue
        last_vote = await handle_voting(bot, game, game.playerlist[uid], vote, voted_msg)
        if last_vote:
            log.info('last vote received, voting closes.')
            break
    await count_votes(bot, game)


async def handle_voting(bot, game, player, vote, voted_msg):
    try:
        answer = "Ja" if vote else "Nein"

        await player.user.send("Thank you for your vote: %s to a President %s and a Chancellor %s" % (answer, game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name))

        await voted_msg.edit(embed=discord.Embed(title="Voted:", description=voted_msg.embeds[0].description + "\n- " + player.name if not voted_msg.embeds[0].description == "*Nobody has voted*" else "- " + player.name))

        log.info("Player %s (%d) voted %s" % (player.name, player.user.id, answer))
        if player.user.id not in game.board.state.last_votes:
            game.board.state.last_votes[player.user.id] = answer
        if len(game.board.state.last_votes) == len(game.player_sequence):
            return True
        return False
    except:
        log.error("handle_voting: Game or board should not be None!")


async def count_votes(bot, game):
    log.info('count_votes called')
    voting_text = ""
    voting_success = False
    for player in game.player_sequence:
        if game.board.state.last_votes[player.user.id] == "Ja":
            voting_text += game.playerlist[player.user.id].name + " voted Ja!\n"
        elif game.board.state.last_votes[player.user.id] == "Nein":
            voting_text += game.playerlist[player.user.id].name + " voted Nein!\n"
    if list(game.board.state.last_votes.values()).count("Ja") > len(game.player_sequence) / 2:  # because player_sequence doesnt include dead
        # VOTING WAS SUCCESSFUL
        log.info("Voting successful")
        voting_text += "Heil President %s! Heil Chancellor %s!" % (
            game.board.state.nominated_president.name, game.board.state.nominated_chancellor.name)
        game.board.state.chancellor = game.board.state.nominated_chancellor
        game.board.state.president = game.board.state.nominated_president
        game.board.state.nominated_president = None
        game.board.state.nominated_chancellor = None
        voting_success = True
        await game.channel.send(voting_text)
        await voting_aftermath(bot, game, voting_success)
    else:
        log.info("Voting failed")
        voting_text += "The people didn't like the two candidates!"
        game.board.state.nominated_president = None
        game.board.state.nominated_chancellor = None
        game.board.state.failed_votes += 1
        if game.board.state.failed_votes == 3:
            await do_anarchy(bot, game)
        else:
            await game.channel.send(voting_text)
            await voting_aftermath(bot, game, voting_success)


async def voting_aftermath(bot, game, voting_success):
    log.info('voting_aftermath called')
    game.board.state.last_votes = {}
    if voting_success:
        if game.board.state.fascist_track >= 3 and game.board.state.chancellor.role == "Hitler":
            # fascists win, because Hitler was elected as chancellor after 3 fascist policies
            game.board.state.game_endcode = -2
            await end_game(bot, game, game.board.state.game_endcode)
        elif game.board.state.fascist_track >= 3 and game.board.state.chancellor.role != "Hitler" and game.board.state.chancellor not in game.board.state.not_hitlers:
            game.board.state.not_hitlers.append(game.board.state.chancellor)
            await draw_policies(bot, game)
        else:
            # voting was successful and Hitler was not nominated as chancellor after 3 fascist policies
            await draw_policies(bot, game)
    else:
        await game.channel.send(game.board.print_board())
        await start_next_round(bot, game)


async def draw_policies(bot, game):
    log.info('draw_policies called')
    game.board.state.veto_refused = False
    # shuffle discard pile with rest if rest < 3
    await shuffle_policy_pile(bot, game)
    for i in range(3):
        game.board.state.drawn_policies.append(game.board.policies.pop(0))

    def check_discard(msg):
        if not msg.author==game.board.state.president.user:
            return False
        validation = validate_message(msg)
        if not validation:
            return False
        cmd, arg = validation
        if not cmd == "discard":
            return False
        try:
            discarded = int(arg)
            if not discarded > 0 or not discarded <= 3:
                return False
        except Exception:
            return False
        return True

    policy_str = ""
    for i, p in enumerate(game.board.state.drawn_policies):
        policy_str += ("[" + str(i+1) + "] " + p + "\n")

    await game.board.state.president.user.send("You drew the following 3 policies:\n{}\nWhich one do you want to discard? Use sh?discard <id>.".format(policy_str))
    try:
        msg = await bot.wait_for('message', check=check_discard, timeout=game.timeout)
        _, arg = validate_message(msg)
        discarded = int(arg)
    except asyncio.TimeoutError:
        log.info('draw_policies timed out - random policy discarded')
        discarded = random.randrange(1, 4)

    await choose_policy(bot, game, game.board.state.drawn_policies[discarded-1])

async def choose_policy(bot, game, answer):
    log.info('choose_policy called')
    try:
        pres = game.board.state.president
        if len(game.board.state.drawn_policies) == 3:
            log.info("Player %s (%d) discarded %s" % (pres.name, pres.user.id, answer))
            await pres.user.send("The policy %s will be discarded!" % answer)
            # remove policy from drawn cards and add to discard pile, pass the other two policies
            for i in range(3):
                if game.board.state.drawn_policies[i] == answer:
                    game.board.discards.append(game.board.state.drawn_policies.pop(i))
                    break
            await pass_two_policies(bot, game)
        elif len(game.board.state.drawn_policies) == 2:
            if answer == "veto":
                log.info("Player %s (%d) suggested a veto" % (game.board.state.chancellor.name, game.board.state.chancellor.user.id))
                await game.board.state.chancellor.user.send("You suggested a Veto to President %s" % game.board.state.president.name)
                await game.channel.send(
                                 "Chancellor %s suggested a Veto to President %s." % (
                                     game.board.state.chancellor.name, game.board.state.president.name))
                await game.board.state.president.user.send("Chancellor %s suggested a Veto to you. Do you want to veto (discard) these cards?" % game.board.state.chancellor.name)
                await game.board.state.president.user.send("Say sh?noveto to accept the suggestion. Say sh?veto to reject it. You have 30 seconds.")
                # veto: if the policy can be passed
                veto = None
                def check_veto(msg):
                    if not msg.author==game.board.state.president.user:
                        return False
                    validation = validate_message(msg)
                    if not validation:
                        return False
                    cmd, _ = validation
                    if cmd == "veto":
                        veto = False
                    elif cmd == "noveto":
                        veto = True
                    else:
                        return False
                    return True
                try:
                    msg = await bot.wait_for('message', check=check_veto, timeout=game.timeout)
                    cmd, _ = validate_message(msg)
                    veto = cmd == "noveto"
                except asyncio.TimeoutError:
                    log.info('choose_policy timed out while waiting for veto, random decision made')
                    veto = random.choice((True, False))
                await choose_veto(bot, game, veto)
            else:
                log.info("Player %s (%d) chose a %s policy" % (game.board.state.chancellor.name, game.board.state.chancellor.user.id, answer))
                await game.board.state.chancellor.user.send("The policy %s will be enacted!" % answer)
                # remove policy from drawn cards and enact, discard the other card
                for i in range(2):
                    if game.board.state.drawn_policies[i] == answer:
                        game.board.state.drawn_policies.pop(i)
                        break
                game.board.discards.append(game.board.state.drawn_policies.pop(0))
                assert len(game.board.state.drawn_policies) == 0
                await enact_policy(bot, game, answer, False)
        else:
            log.error("choose_policy: drawn_policies should be 3 or 2, but was " + str(len(game.board.state.drawn_policies)))
    except:
        log.error("choose_policy: Game or board should not be None!")


async def pass_two_policies(bot, game):
    log.info('pass_two_policies called')

    policy_str = ""
    for i, p in enumerate(game.board.state.drawn_policies):
        policy_str += ("[" + str(i+1) + "] " + p + "\n")

    veto = False
    def check_policies(msg):
        if not msg.author==game.board.state.chancellor.user:
            return False
        validation = validate_message(msg)
        if not validation:
            return False
        cmd, arg = validation
        if cmd == "enact":
            try:
                id = int(arg)
                if id > 0 and id <= len(game.board.state.drawn_policies):
                    return True
            except Exception:
                return False
        elif cmd == "veto":
            veto = True
        else:
            return False
        return True

    def check_policies_noveto(msg):
        if not msg.author==game.board.state.chancellor.user:
            return False
        validation = validate_message(msg)
        if not validation:
            return False
        cmd, arg = validation
        if cmd == "enact":
            try:
                id = int(arg)
                if id > 0 and id <= len(game.board.state.drawn_policies):
                    return True
            except Exception:
                return False
        else:
            return False

        return True

    if game.board.state.fascist_track == 5 and not game.board.state.veto_refused:
        await game.channel.send(
                         "President %s gave two policies to Chancellor %s." % (
                             game.board.state.president.name, game.board.state.chancellor.name))

        await game.board.state.chancellor.user.send("President %s gave you the following 2 policies:\n%s\n Enact one of them using sh?enact <id>. You can also use your Veto power: sh?veto. You have 30 seconds." % (game.board.state.president.name, policy_str))

        try:
            msg = await bot.wait_for('message', check=check_policies, timeout=game.timeout)
            cmd, arg = validate_message(msg)
            if cmd == "veto":
                enacted_policy = "veto"
            else:
                enacted_policy = game.board.state.drawn_policies[int(arg)-1]
        except asyncio.TimeoutError:
            log.info('pass_two_policies timed out - random policy enacted')
            enacted_policy = game.board.state.drawn_policies[random.randrange(1,3)]
        await choose_policy(bot, game, enacted_policy)

    else:
        if game.board.state.veto_refused:
            await game.board.state.chancellor.user.send("President {} refused your Veto. Now you have to choose from the following policies:\n{}\nWhich one do you want to enact? Use sh?enact <id>".format(game.board.state.president.name, policy_str))
        elif game.board.state.fascist_track < 5:
            await game.board.state.chancellor.user.send("President {} gave you the following 2 policies:\n{}\nWhich one do you want to enact? Use sh?enact <id>".format(game.board.state.president.name, policy_str))

        try:
            msg = await bot.wait_for('message', check=check_policies_noveto, timeout=game.timeout)
            _, arg = validate_message(msg)
            enacted = int(arg)
        except asyncio.TimeoutError:
            log.info('pass_two_policies timed out - random policy enacted')
            enacted = random.randrange(1,3)
        await choose_policy(bot, game, game.board.state.drawn_policies[enacted-1])


async def enact_policy(bot, game, policy, anarchy):
    log.info('enact_policy called')
    if policy == "liberal":
        game.board.state.liberal_track += 1
    elif policy == "fascist":
        game.board.state.fascist_track += 1
    game.board.state.failed_votes = 0  # reset counter
    if not anarchy:
        await game.channel.send(
                         "President %s and Chancellor %s enacted a %s policy!" % (
                             game.board.state.president.name, game.board.state.chancellor.name, policy))
    else:
        await game.channel.send(
                         "The top most policy was enacted: %s" % policy)
    sleep(3)
    await game.channel.send(game.board.print_board())
    # end of round
    if game.board.state.liberal_track == 5:
        game.board.state.game_endcode = 1
        await end_game(bot, game, game.board.state.game_endcode)  # liberals win with 5 liberal policies
    if game.board.state.fascist_track == 6:
        game.board.state.game_endcode = -1
        await end_game(bot, game, game.board.state.game_endcode)  # fascists win with 6 fascist policies
    sleep(3)
    if not anarchy:
        if policy == "fascist":
            action = game.board.fascist_track_actions[game.board.state.fascist_track - 1]
            if action is None and game.board.state.fascist_track == 6:
                pass
            elif action == None:
                await start_next_round(bot, game)
            elif action == "policy":
                await game.channel.send(
                                 "Presidential Power enabled: Policy Peek " + u"\U0001F52E" + "\nPresident " + game.board.state.president.name + " now knows the next three policies on "
                                                                                                                                                 "the pile.  The President may share "
                                                                                                                                                 "(or lie about!) the results of their "
                                                                                                                                                 "investigation at their discretion.")
                await action_policy(bot, game)
            elif action == "kill":
                await game.channel.send(
                                 "Presidential Power enabled: Execution " + u"\U0001F5E1" + "\nPresident " + game.board.state.president.name + " has to kill one person. You can "
                                                                                                                                               "discuss the decision now but the "
                                                                                                                                               "President has the final say.")
                await action_kill(bot, game)
            elif action == "inspect":
                await game.channel.send(
                                 "Presidential Power enabled: Investigate Loyalty " + u"\U0001F50E" + "\nPresident " + game.board.state.president.name + " may see the party membership of one "
                                                                                                                                                         "player. The President may share "
                                                                                                                                                         "(or lie about!) the results of their "
                                                                                                                                                         "investigation at their discretion.")
                await action_inspect(bot, game)
            elif action == "choose":
                await game.channel.send(
                                 "Presidential Power enabled: Call Special Election " + u"\U0001F454" + "\nPresident " + game.board.state.president.name + " gets to choose the next presidential "
                                                                                                                                                           "candidate. Afterwards the order resumes "
                                                                                                                                                           "back to normal.")
                await action_choose(bot, game)
        else:
            await start_next_round(bot, game)
    else:
        await start_next_round(bot, game)


async def choose_veto(bot, game, veto):
    log.info('choose_veto called')
    # remember, veto is True if policy is accepted
    answer = "yesveto" if veto else "noveto"
    try:
        uid = game.board.state.president.user.id
        if answer == "yesveto":
            log.info("Player %s (%d) accepted the veto" % (game.board.state.president.name, uid))
            await game.board.state.president.user.send("You accepted the Veto!")
            await game.channel.send(
                             "President %s accepted Chancellor %s's Veto. No policy was enacted but this counts as a failed election." % (
                                 game.board.state.president.name, game.board.state.chancellor.name))
            game.board.discards += game.board.state.drawn_policies
            game.board.state.drawn_policies = []
            game.board.state.failed_votes += 1
            if game.board.state.failed_votes == 3:
                await do_anarchy(bot, game)
            else:
                await game.channel.send(game.board.print_board())
                await start_next_round(bot, game)
        elif answer == "noveto":
            log.info("Player %s (%d) declined the veto" % (game.board.state.president.name, uid))
            game.board.state.veto_refused = True
            await game.board.state.president.user.send("You refused the Veto!")
            await game.channel.send(
                             "President %s refused Chancellor %s's Veto. The Chancellor now has to choose a policy!" % (
                                 game.board.state.president.name, game.board.state.chancellor.name))
            await pass_two_policies(bot, game)
        else:
            log.error("choose_veto: Callback data can either be \"yesveto\" or \"noveto\", but not %s" % answer)
    except:
        log.error("choose_veto: Game or board should not be None!")


async def do_anarchy(bot, game):
    log.info('do_anarchy called')
    await game.channel.send(game.board.print_board())
    await game.channel.send("**ANARCHY!**")
    top_policy = game.board.policies.pop(0)
    game.board.state.last_votes = {}
    await enact_policy(bot, game, top_policy, True)


async def action_policy(bot, game):
    log.info('action_policy called')
    topPolicies = ""
    # shuffle discard pile with rest if rest < 3
    await shuffle_policy_pile(bot, game)
    for i in range(3):
        topPolicies += game.board.policies[i] + "\n"
    await game.board.state.president.user.send(
                     "The top three polices are (top most first):\n%s\nYou may lie about this." % topPolicies)
    await start_next_round(bot, game)


async def action_kill(bot, game):
    log.info('action_kill called')
    btns = []
    for uid in game.playerlist:
        if uid != game.board.state.president.user.id and game.playerlist[uid].is_dead == False:
            name = game.playerlist[uid].name
            btns.append({'name': name, 'uid': uid})

    await game.board.state.president.user.send(game.board.print_board())
    await game.board.state.president.user.send(
        "You have to kill one person. You can discuss your decision with the others. Choose wisely!\nUse sh?kill <id> to kill.\n{}\nYou have 30 seconds.".format(
            "\n".join("[" + str(i+1) + "] " + p['name'] for i, p in enumerate(btns))
            )
    )
    def check_kill(msg):
        if not msg.author==game.board.state.president.user:
            return False
        validation = validate_message(msg)
        if not validation:
            return False
        cmd, arg = validation
        if cmd == "kill":
            try:
                id = int(arg)
                if id > 0 and id <= len(btns):
                    return True
            except Exception:
                return False
        else:
            return False
    try:
        msg = await bot.wait_for('message', check=check_kill, timeout=game.timeout)
        cmd, arg = validate_message(msg)
        killed_id = int(arg)
    except asyncio.TimeoutError:
        log.info('action_kill timed out - random victim chosen')
        killed_id = random.choice([i for i, p in enumerate(btns)])
    killed_uid = btns[killed_id-1]['uid']
    await choose_kill(bot, game, killed_uid)


async def choose_kill(bot, game, answer):
    log.info('choose_kill called')
    try:
        chosen = game.playerlist[answer]
        chosen.is_dead = True
        if game.player_sequence.index(chosen) <= game.board.state.player_counter:
            game.board.state.player_counter -= 1
        game.player_sequence.remove(chosen)
        game.board.state.dead += 1
        log.info("Player %s (%d) killed %s (%d)" % (
            game.board.state.president.name, game.board.state.president.user.id, chosen.name, chosen.user.id))
        await game.board.state.president.user.send("You killed %s!" % chosen.name)
        if chosen.role == "Hitler":
            await game.channel.send("President " + game.board.state.president.name + " killed " + chosen.name + ". ")
            await end_game(bot, game, 2)
        else:
            await game.channel.send(
                             "President %s killed %s who was not Hitler. <@%s>, you are dead now and are not allowed to talk anymore!" % (
                                 game.board.state.president.name, chosen.name, chosen.user.id))
            await game.channel.send(game.board.print_board())
            await start_next_round(bot, game)
    except:
        log.error("choose_kill: Game or board should not be None!")


async def action_choose(bot, game):
    log.info('action_choose called')
    btns = []
    for uid in game.playerlist:
        if uid != game.board.state.president.user.id and game.playerlist[uid].is_dead == False:
            name = game.playerlist[uid].name
            btns.append({'name': name, 'uid': uid})
    def check_choose(msg):
        if not msg.author==game.board.state.president.user:
            return False
        validation = validate_message(msg)
        cmd, arg = validation
        if cmd == "choose":
            try:
                id = int(arg)
                if id > 0 and id <= len(btns):
                    return True
            except Exception:
                return False
        else:
            return False

        return True

    await game.board.state.president.user.send(game.board.print_board())
    await game.board.state.president.user.send('You get to choose the next presidential candidate. Afterwards the order resumes back to normal. Choose wisely! Your choices are:\n{}\n You have 30 seconds. Use sh?choose <id>'
                                               .format(
                                                   "\n".join("[" + str(i+1) + "]" + p['name'] for i, p in enumerate(btns))
                                               )
    )

    try:
        msg = await bot.wait_for('message', check=check_choose, timeout=game.timeout)
        _, arg = validate_message(msg)
        chosen_id = int(arg)
    except asyncio.TimeoutError:
        log.info('action_choose timed out - random president chosen')
        chosen_id = random.choice([i for i in range(1, len(btns)+1)])
    chosen_uid = btns[chosen_id-1]['uid']
    await choose_choose(bot, game, chosen_uid)

async def choose_choose(bot, game, answer):
    log.info('choose_choose called')
    try:
        chosen = game.playerlist[answer]
        game.board.state.chosen_president = chosen
        log.info(
            "Player %s (%d) chose %s (%d) as next president" % (
                game.board.state.president.name, game.board.state.president.user.id, chosen.name, chosen.user.id))
        await game.board.state.president.user.send("You chose %s as the next president!" % chosen.name)
        await game.channel.send("President %s chose %s as the next president." % (game.board.state.president.name, chosen.name))
        await start_next_round(bot, game)
    except:
        log.error("choose_choose: Game or board should not be None!")


async def action_inspect(bot, game):
    log.info('action_inspect called')
    btns = []
    for i, uid in enumerate(game.playerlist):
        if uid != game.board.state.president.user.id and game.playerlist[uid].is_dead == False:
            name = game.playerlist[uid].name
            btns.append({'name': name, 'uid': uid})
    def check_inspect(msg):
        if not msg.author==game.board.state.president.user:
            return False
        validation = validate_message(msg)
        cmd, arg = validation
        if cmd == "inspect":
            try:
                id = int(arg)
                if id > 0 and id <= len(game.playerlist):
                    return True
            except Exception:
                return False
        else:
            return False

        return True

    await game.board.state.president.user.send(game.board.print_board())
    await game.board.state.president.user.send('You may see the party membership of one player. Which do you want to know? Choose wisely!\nYour choices are:{}\n\n You have 30 seconds. Use sh?inspect <id>.'
                                               .format(
                                                   "\n".join("[" + str(i+1) + "]" + p['name'] for i, p in enumerate(btns))
                                               )
    )
    try:
       msg =  await bot.wait_for('message', check=check_inspect, timeout=game.timeout)
       _, arg = validate_message(msg)
       inspect_id = int(arg)
    except asyncio.TimeoutError:
        log.info('action_inspect timed out - random target chosen')
        inspect_id = random.choice([i for i in range(1, len(btns)+1)])
    inspect_uid = btns[inspect_id-1]['uid']
    await choose_inspect(bot, game, inspect_uid)


async def choose_inspect(bot, game, answer):
    log.info('choose_inspect called')
    try:
        chosen = game.playerlist[answer]
        log.info("Player %s (%d) inspects %s (%d)'s party membership: %s" % (
                game.board.state.president.name, game.board.state.president.user.id, chosen.name, chosen.user.id,
                chosen.party))
        await game.board.state.president.user.send("The party membership of %s is %s" % (chosen.name, chosen.party))
        await game.channel.send("President %s inspected %s." % (game.board.state.president.name, chosen.name))
        await start_next_round(bot, game)
    except:
        log.error("choose_inspect: Game or board should not be None!")


async def start_next_round(bot, game):
    log.info('start_next_round called')
    # start next round if there is no winner (or sh?cancel)
    if game.board.state.game_endcode == 0:
        # start new round
        sleep(5)
        # if there is no special elected president in between
        if game.board.state.chosen_president is None:
            increment_player_counter(game)
        await start_round(bot, game)


##
#
# End of round
#
##

async def end_game(bot, game, game_endcode):
    log.info('end_game called')
    ##
    # game_endcode:
    #   -2  fascists win by electing Hitler as chancellor
    #   -1  fascists win with 6 fascist policies
    #   0   not ended
    #   1   liberals win with 5 liberal policies
    #   2   liberals win by killing Hitler
    #   99  game cancelled
    ##
    with open("stats.json", 'r') as f:
        stats = json.load(f)

    if game_endcode == 99:
        if games[game.channel.id].board is not None:
            await game.channel.send(
                             "Game cancelled!\n\n%s" % game.print_roles())
            # bot.send_message(ADMIN, "Game of Secret Hitler canceled in group %d" % game.channel)
            stats['cancelled'] = stats['cancelled'] + 1
        else:
            await game.channel.send("Game cancelled!")
    else:
        if game_endcode == -2:
            await game.channel.send(
                             "Game over! The fascists win by electing Hitler as Chancellor!\n\n%s" % game.print_roles())
            stats['fascwin_hitler'] = stats['fascwin_hitler'] + 1
        if game_endcode == -1:
            await game.channel.send(
                             "Game over! The fascists win by enacting 6 fascist policies!\n\n%s" % game.print_roles())
            stats['fascwin_policies'] = stats['fascwin_policies'] + 1
        if game_endcode == 1:
            await game.channel.send(
                             "Game over! The liberals win by enacting 5 liberal policies!\n\n%s" % game.print_roles())
            stats['libwin_policies'] = stats['libwin_policies'] + 1
        if game_endcode == 2:
            await game.channel.send(
                             "Game over! The liberals win by killing Hitler!\n\n%s" % game.print_roles())
            stats['libwin_kill'] = stats['libwin_kill'] + 1

        # bot.send_message(ADMIN, "Game of Secret Hitler ended in group %d" % game.channel)

    with open("stats.json", 'w') as f:
        json.dump(stats, f)
    del games[game.channel.id]


async def inform_players(bot, game, player_number):
    log.info('inform_players called')
    await game.channel.send(
                     "Let's start the game with %d players!\n%s\nGo to your private chat and look at your secret role!" % (
                         player_number, print_player_info(player_number)))
    available_roles = list(players[player_number]["roles"])  # copy not reference because we need it again later
    for uid in game.playerlist:
        random_index = randrange(len(available_roles))
        role = available_roles.pop(random_index)
        party = get_membership(role)
        game.playerlist[uid].role = role
        game.playerlist[uid].party = party
        await game.playerlist[uid].user.send("Your secret role is: %s\nYour party membership is: %s" % (role, party))


def print_player_info(player_number):
    if player_number == 5:
        return "There are 3 Liberals, 1 Fascist and Hitler. Hitler knows who the Fascist is."
    elif player_number == 6:
        return "There are 4 Liberals, 1 Fascist and Hitler. Hitler knows who the Fascist is."
    elif player_number == 7:
        return "There are 4 Liberals, 2 Fascists and Hitler. Hitler doesn't know who the Fascists are."
    elif player_number == 8:
        return "There are 5 Liberals, 2 Fascists and Hitler. Hitler doesn't know who the Fascists are."
    elif player_number == 9:
        return "There are 5 Liberals, 3 Fascists and Hitler. Hitler doesn't know who the Fascists are."
    elif player_number == 10:
        return "There are 6 Liberals, 3 Fascists and Hitler. Hitler doesn't know who the Fascists are."
    elif player_number == 3:
        return "There is 1 Liberal, 1 Fascist and Hitler. Hitler doesn't know who the Fascist is. This is only for testing."
    elif player_number == 4:
        return "There is 2 Liberals, 1 Fascist and Hitler. Hitler doesn't know who the Fascist is. This is only for testing."


async def inform_fascists(bot, game, player_number):
    log.info('inform_fascists called')
    if player_number == 5 or player_number == 6:
        for uid in game.playerlist:
            role = game.playerlist[uid].role
            if role == "Hitler":
                fascists = game.get_fascists()
                if len(fascists) > 1:
                    await game.playerlist[uid].user.send("Error. There should be only one Fascist in a 5/6 player game!")
                else:
                    await game.playerlist[uid].user.send("Your fellow fascist is: %s" % fascists[0].name)
            elif role == "Fascist":
                hitler = game.get_hitler()
                await game.playerlist[uid].user.send("Hitler is: %s" % hitler.name)
            elif role == "Liberal":
                pass
            else:
                log.error("inform_fascists: can\'t handle the role %s" % role)

    else:
        for uid in game.playerlist:
            role = game.playerlist[uid].role
            if role == "Fascist":
                fascists = game.get_fascists()
                if len(fascists) == 1:
                    await game.playerlist[uid].user.send("Error: There should be more than one Fascist in a 7/8/9/10 player game!")
                else:
                    fstring = ""
                    for f in fascists:
                        if f.user.id != uid:
                            fstring += f.name + ", "
                    fstring = fstring[:-2]
                    await game.playerlist[uid].user.send("Your fellow fascists are: %s" % fstring)
                    hitler = game.get_hitler()
                    await game.playerlist[uid].user.send("Hitler is: %s" % hitler.name)
            elif role == "Hitler":
                pass
            elif role == "Liberal":
                pass
            else:
                log.error("inform_fascists: can\'t handle the role %s" % role)


def get_membership(role):
    log.info('get_membership called')
    if role == "Fascist" or role == "Hitler":
        return "fascist"
    elif role == "Liberal":
        return "liberal"
    else:
        return None


def increment_player_counter(game):
    log.info('increment_player_counter called')
    if game.board.state.player_counter < len(game.player_sequence) - 1:
        game.board.state.player_counter += 1
    else:
        game.board.state.player_counter = 0


async def shuffle_policy_pile(bot, game):
    log.info('shuffle_policy_pile called')
    if len(game.board.policies) < 3:
        game.board.discards += game.board.policies
        game.board.policies = random.sample(game.board.discards, len(game.board.discards))
        game.board.discards = []
        await game.channel.send(
                         "There were not enough cards left on the policy pile so I shuffled the rest with the discard pile!")

def validate_message(msg):
    """
    Returns False if not a valid command. Otherwise return the command and the first argument.
    """
    msg_content = msg.content.strip()
    if not msg_content.lower().startswith(PREFIX):
        return False
    cmd, *args = msg_content.split()
    cmd = cmd[len(PREFIX):].lower().strip()
    arg = args[0] if len(args) else None
    return (cmd, arg)
