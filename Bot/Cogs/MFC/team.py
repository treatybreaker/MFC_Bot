import logging

import discord

from Bot import APIRequest
from Bot.Cogs import BaseCog
from Bot.Cogs import command
from Bot.Config.Permissions import Permissions

log = logging.getLogger(__name__)


class MatchPlanning(BaseCog):

    @command.group(aliases=["t"])
    @Permissions.is_permitted()
    async def team(self, ctx: command.Context):
        """A group containing all MFC team related commands"""

    @team.group(aliases=["p"])
    @Permissions.is_permitted()
    async def player(self, ctx: command.Context):
        """A sub  group of team containing player related team commands, must be used in a server"""
        if not ctx.guild:
            await ctx.send(f"This command can only be used within a discord server.")
            return

    @player.command(aliases=["a"])
    @Permissions.is_permitted()
    async def add(self, ctx: command.Context, player: discord.Member, team: discord.Role):
        """Adds a player to a team if they've been registered as a player previously."""
        team_lookup = await APIRequest.get(f"/team/discord-id?discord_id={team.id}")
        if team_lookup.status == 404:
            await ctx.send(f"Could not find a team with discord id: `{team.id}`")
            return
        elif team_lookup.status != 200:
            await ctx.send(f"Unable to receive data from the API, something has gone wrong!")
            return
        team_id = team_lookup.json["id"]
        player_lookup = await APIRequest.get(f"/player/discord-id?discord_id={player.id}")
        if player_lookup.status == 404:
            await ctx.send(f"Could not find a player with discord id: `{player.id}`")
            return
        elif player_lookup.status != 200:
            await ctx.send(f"Unable to receive data from the API, something has gone wrong!")
            return
        player_id = player_lookup.json["id"]
        add_player = await APIRequest.post(f"/team/add-player-to-team?player_id={player_id}&team_id={team_id}")
        if add_player.status == 403:
            await ctx.send(f"Could not authenticate with the API")
            return
        elif add_player.status != 200:
            await ctx.send(f"Unable to receive data from the API, something has gone wrong!")
            return
        await ctx.send(f"Added player to team")
        

    @team.command(aliases=["c"])
    @Permissions.is_permitted()
    async def create(self, ctx: command.Context, discord_team_role: discord.Role, team_elo: int):
        """Creates a team"""
        response = await APIRequest.post(
            "/team/create",
            data={
                "team_name": discord_team_role.name,
                "discord_id": discord_team_role.id,
                "elo": team_elo
            }
        )
        if response.status == 403:
            await ctx.send(f"Could not authenticate with the API")
            return
        elif response.status == 409:
            await ctx.send(f"The team `{discord_team_role.name}` already exists!")
            return
        elif response.status != 200:
            await ctx.send(f"Unable to send the data to the API, something has gone wrong!")
            return
        team_id = response.json["extra"][0]["id"]
        await ctx.send(f"Created the team `{discord_team_role.name}` with ID: `{team_id}`")
        log.info(f"{ctx.author} ({ctx.author.id}) created the team {discord_team_role.name}, API id: {team_id}")

    @team.command(aliases=["d"])
    @Permissions.is_permitted()
    async def delete(self, ctx: command.Context, discord_team_role: discord.Role):
        """Deletes a team"""
        team_id = await APIRequest.get(f"/team/discord-id?discord_id={discord_team_role.id}")
        if team_id.status == 404:
            await ctx.send(f"Could not find a team with name: `{discord_team_role.name}`. "
                           f"It may have been renamed outside of the command functions or never added.")
            return
        elif team_id.status != 200:
            await ctx.send(f"Something went wrong on the API!")
            return
        team_id = team_id.json["id"]
        response = await APIRequest.post(f"/team/delete?team_id={team_id}")
        if response.status == 404:
            await ctx.send(f"Could not find that team!")
            return
        elif response.status == 403:
            await ctx.send(f"Could not authenticate with the API!")
            return
        await ctx.send(f"Deleted the team `{discord_team_role.name}`")
        log.info(f"{ctx.author} ({ctx.author.id}) deleted the team {discord_team_role.name}, API id: {team_id}")