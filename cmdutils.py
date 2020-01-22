from discord.ext.commands import check, Context, CheckFailure


class NotGuildOwner(CheckFailure):
    """Exception raised when the message author is not the owner of the guild.

    This inherits from :exc:`CheckFailure`
    """
    pass


def is_guild_owner():
    """A :func:`.check` that checks if the person invoking this command is the
    owner of the guild.

    This is powered by :meth:`.Guild.owner`.

    This check raises a special exception, :exc:`.NotGuildOwner` that is derived
    from :exc:`.CheckFailure`.
    """

    async def predicate(ctx: Context):
        if not ctx.author == ctx.guild.owner:
            raise NotGuildOwner('You do not own this guild.')
        return True

    return check(predicate)
