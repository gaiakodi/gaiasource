# -*- coding: utf-8 -*-

'''
	Gaia Add-on
	Copyright (C) 2016 Gaia

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

'''
	Previously free accounts could access the API.
	But when tested, the API returns an error saying this is only available for premium accounts.
	Contacted WriteSonic asking about this and if there are free developer accounts.
	They replied that API access was revoked for free accounts due to abuse, but did not say anything about developer accounts.
	Sent them another email asking specifically about developer accounts.
	After a week they still have not replied.
	So fuck them, we are not going to support their stuff.
'''

from lib.oracle import Oracle

class Chatsonic(Oracle):

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		Oracle.__init__(self,
			id				= 'chatsonic',
			name			= 'ChatSonic',
			organization	= 'WriteSonic',

			type			= Oracle.TypeChatbot,
			subscription	= Oracle.SubscriptionPaid,
			intelligence	= Oracle.IntelligenceHigh,
			rating			= 4,
			color			= 'FFA128FF',

			linkWeb			= 'https://writesonic.com/chat',
			linkApi			= 'https://api.writesonic.com/v2/business/content/chatsonic',
			linkAccount		= 'https://app.writesonic.com',
		)
