"""Configuration for a Discord ~~server~~ guild"""  
from dataclasses import dataclass
from typing import List, Optional

from discord import Member, Role


@dataclass
class GuildConfig:
    """Stuff about the guild"""

    guild_id: str              # guild id
    name: str                  # guild name
    override: List[int]        # no bad-boy
    pariah: List[int]          # bad-boy timeout
    admin_role: Optional[int]  # guild role to administer the bot
    edit_role: Optional[int]   # guild role to edit templates

    def can_admin(self, member: Member) -> bool:
        """determine if the provided user can administer the bot"""
        return member.id not in self.pariah and (member.id in self.override or member.guild_permissions.administrator or any(r for r in member.roles if r.id == self.admin_role))

    def can_edit(self, member: Member) -> bool:
        """determine if the provided user can edit memes"""
        return member.id not in self.pariah and (member.id in self.override or member.guild_permissions.administrator or any(r for r in member.roles if r.id == self.edit_role))

    def can_use(self, member: Member) -> bool:
        """determine if the provided user is a bad boy"""
        return member.id not in self.pariah

    def set_admin_role(self, member: Member, role: Role=None) -> str:
        """set the role if of the role permitted to administer the bot"""
        if not self.can_admin(member):
            return self.no_admin(member)
        self.admin_role = role.id if role is not None else None
        return f"Members of '{role}' are now authorized to administer the memes."

    def set_edit_role(self, member: Member, role: Role) -> str:
        """set the role if of the role permitted to edit memes"""
        if not self.can_admin(member):
            return self.no_admin(member)
        self.edit_role = role.id if role is not None else None
        return f"Members of '{role}' are now authorized to edit the memes."

    def shun(self, member: Member, victim: Member) -> str:
        """make someone a bad boy"""
        if not self.can_admin(member):
            return self.no_admin(member)
        elif member == victim:
            self.pariah.append(victim.id)
            return "If that's what you really want to do."
        elif victim.id in self.override:
            self.pariah.append(member.id)
            return f"{self.member_nick(member)}. Your membership to The Continental has been, by thine own hand, revoked."
        elif not member.id in self.override and victim.guild_permissions.administrator:
            return "As fun as it sounds, it's probably not a good idea."
        else:
            self.pariah.append(victim.id)
            return f"{self.member_nick(victim)} is now excommunicado"

    def endorse(self, member: Member, victim: Member) -> str:
        """make someone a good boy"""
        if member.id == victim.id and victim.id in self.pariah and (member.id in self.override or member.guild_permissions.administrator):
            self.pariah.remove(victim.id)
            return "Wait, you can do that?"
        elif not self.can_admin(member):
            return self.no_admin(member)
        elif victim.id in self.pariah:
            self.pariah.remove(victim.id)
            return f"The contract on {self.member_nick(victim)} has been cancelled"
        else:
            return "/okay"

    def member_full_name(self, member: Member) -> str:
        """format a user's name"""
        return f"{member.nick} ({member.name}#{member.discriminator})" if member.nick else f"{member.name}#{member.discriminator}"

    def member_nick(self, member: Member) -> str:
        """format a user's nickname"""
        return f"{member.nick}" if member.nick else f"{member.name}"

    def no_admin(self, member: Member, action='administer', permission='admin') -> str:
        """format an error for failing to admin the bot"""
        return f"Therapist: What do we do when we feel powerless and depressed?\n\n{self.member_nick(member)}: Try to {action} the bot without {permission} rights.\n\nTherapist: No."

    def no_memes(self) -> str:
        return "No memes for you!"

    def __hash__(self):
        return hash(self.guild_id)

    def __eq__(self, other):
        return self.guild_id == other.guild_id