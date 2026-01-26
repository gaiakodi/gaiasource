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

# https://platform.openai.com/docs/

#gaiaremove - test Chatgpt 4 - https://community.openai.com/t/gpt-4-model-does-not-exist/291988 - seems that OpenAI has only opened GPT4 to paying customers, not the free $5 accounts.

from lib.oracle import Oracle
from lib.modules.tools import Media, Time, Tools, Math, Regex, Logger, Settings, Converter, Hash
from lib.modules.interface import Dialog, Format, Font, Translation
from lib.modules.network import Networker
from lib.modules.convert import ConverterTime, ConverterDuration
from lib.modules.account import Openai as Account

class Chatgpt(Oracle):

	ActionChat			= 'chat'
	ActionCompletions	= 'completions'

	ReleaseStable		= 'stable'				# Available to the public.
	ReleaseAlpha		= 'alpha'				# Available to selected users.
	ReleaseBeta			= 'beta'				# Available to selected users.
	ReleaseCategory		= 'category'			# Use parent category release.
	Releases			= [
		{
			'id'			: ReleaseStable,
			'name'			: 'Stable',
			'description'	: 'Available to all public users.',
		},
		{
			'id'			: ReleaseAlpha,
			'name'			: 'Alpha',
			'description'	: 'Available only to alpha testers.',
		},
		{
			'id'			: ReleaseBeta,
			'name'			: 'Beta',
			'description'	: 'Available only to beta testers.',
		},
	]

	CategoryGpt40		= 'gpt-4.0'
	CategoryGpt35		= 'gpt-3.5'
	CategoryGpt30		= 'gpt-3.0'
	Categories			= [
		{
			'id'			: CategoryGpt40,
			'name'			: 'GPT-4.0',
			'description'	: 'Large multimodal models that can solve difficult problems with great accuracy.',
			'release'		: ReleaseStable,
			'refine'		: True,
		},
		{
			'id'			: CategoryGpt35,
			'name'			: 'GPT-3.5',
			'description'	: 'Capable and cost effective models that can understand and generate natural language.',
			'release'		: ReleaseStable,
			'refine'		: True,
		},
		{
			'id'			: CategoryGpt30,
			'name'			: 'GPT-3.0',
			'description'	: 'Less capable but cost effective models that can understand and generate natural language.',
			'release'		: ReleaseStable,
			'refine'		: True, # Combine previous messages into a single long newline-separated question.
		},
	]

	# /v1/chat/completions
	ModelGpt4			= 'gpt-4'				# (Max Tokens: 8,192 | Training: Sep 2021 | $0.06/1K tokens) More capable than any GPT-3.5 model, able to do more complex tasks, and optimized for chat. Will be updated with our latest model iteration.
	ModelGpt432k		= 'gpt-4-32k'			# (Max Tokens: 32,768 | Training: Sep 2021 | $0.12/1K tokens) Same capabilities as the base gpt-4 mode but with 4x the context length. Will be updated with our latest model iteration.
	ModelGpt35Turbo		= 'gpt-3.5-turbo'		# (Max Tokens: 4,096 | Training: Sep 2021 | $0.002/1K tokens) Most capable GPT-3.5 model and optimized for chat at 1/10th the cost of text-davinci-003. Will be updated with our latest model iteration.
	# /v1/completions
	ModelTextDavinci3	= 'text-davinci-003'	# (Max Tokens: 4,097 | Training: Jun 2021) Can do any language task with better quality, longer output, and consistent instruction-following than the curie, babbage, or ada models. Also supports inserting completions within text.
	ModelTextDavinci2	= 'text-davinci-002'	# (Max Tokens: 4,097 | Training: Jun 2021) Similar capabilities to text-davinci-003 but trained with supervised fine-tuning instead of reinforcement learning
	ModelTextCurie1		= 'text-curie-001'		# (Max Tokens: 2,049 | Training: Oct 2019) Very capable, faster and lower cost than Davinci.
	ModelTextBabbage1	= 'text-babbage-001'	# (Max Tokens: 2,049 | Training: Oct 2019) Capable of straightforward tasks, very fast, and lower cost.
	ModelTextAda1		= 'text-ada-001'		# (Max Tokens: 2,049 | Training: Oct 2019) Capable of very simple tasks, usually the fastest model in the GPT-3 series, and lowest cost.
	ModelDavinci		= 'davinci'				# (Max Tokens: 2,049 | Training: Oct 2019 | $0.0200/1K tokens) Most capable GPT-3 model. Can do any task the other models can do, often with higher quality.
	ModelCurie			= 'curie'				# (Max Tokens: 2,049 | Training: Oct 2019 | $0.0020/1K tokens) Very capable, but faster and lower cost than Davinci.
	ModelBabbage		= 'babbage'				# (Max Tokens: 2,049 | Training: Oct 2019 | $0.0005/1K tokens) Capable of straightforward tasks, very fast, and lower cost.
	ModelAda			= 'ada'					# (Max Tokens: 2,049 | Training: Oct 2019 | $0.0004/1K tokens) Capable of very simple tasks, usually the fastest model in the GPT-3 series, and lowest cost.

	ModelDefault		= ModelGpt35Turbo
	Models				= [
		{
			'id'			:	ModelGpt4,
			'category'		:	CategoryGpt40,
			'release'		:	ReleaseCategory,
			'name'			:	'Base',
			'description'	:	'Most capable model for complex tasks with optimized chat.',
			'explanation'	:	'More capable than any GPT-3.5 model, able to do more complex tasks, and optimized for chat. Will be updated with the latest model iteration.',
			'limit'			:	8192,
			'time'			:	1632960000,
			'price'			:	0.0600,
			'action'		:	[ActionChat, ActionCompletions],
		},
		{
			'id'			:	ModelGpt432k,
			'category'		:	CategoryGpt40,
			'release'		:	ReleaseCategory,
			'name'			:	'Base 32K',
			'description'	:	'Same as the base GPT-4 but with longer output.',
			'explanation'	:	'Same capabilities as the base GPT-4 mode but with 4 times the context length. Will be updated with the latest model iteration.',
			'limit'			:	32768,
			'time'			:	1632960000,
			'price'			:	0.1200,
			'action'		:	[ActionChat, ActionCompletions],
		},
		{
			'id'			:	ModelGpt35Turbo,
			'category'		:	CategoryGpt35,
			'release'		:	ReleaseCategory,
			'name'			:	'Turbo',
			'description'	:	'Most capable GPT-3.5 model with optimized chat at lower cost.',
			'explanation'	:	'Most capable GPT-3.5 model and optimized for chat at 10th of the cost of Text Davinci 3. Will be updated with the latest model iteration.',
			'limit'			:	4096,
			'time'			:	1632960000,
			'price'			:	0.0020,
			'action'		:	[ActionChat, ActionCompletions],
		},
		{
			'id'			:	ModelTextDavinci3,
			'category'		:	CategoryGpt35,
			'release'		:	ReleaseCategory,
			'name'			:	'Text Davinci 3',
			'description'	:	'Capable model with better quality and longer output.',
			'explanation'	:	'Can do any language task with better quality, longer output, and consistent instruction following than the Curie, Babbage, or Ada models. Also supports inserting completions within text.',
			'limit'			:	4097,
			'time'			:	1625011200,
			'price'			:	0.0200,
			'action'		:	[ActionCompletions],
		},
		{
			'id'			:	ModelTextDavinci2,
			'category'		:	CategoryGpt35,
			'release'		:	ReleaseCategory,
			'name'			:	'Text Davinci 2',
			'description'	:	'Similar to Text Davinci 3 trained with supervised fine-tuning.',
			'explanation'	:	'Similar capabilities to Text Davinci 3 but trained with supervised fine-tuning instead of reinforcement learning.',
			'limit'			:	4097,
			'time'			:	1625011200,
			'price'			:	0.0200,
			'action'		:	[ActionCompletions],
		},
		{
			'id'			:	ModelTextCurie1,
			'category'		:	CategoryGpt30,
			'release'		:	ReleaseCategory,
			'name'			:	'Text Curie 1',
			'description'	:	'Capable model faster and cheaper than Davinci.',
			'explanation'	:	'Very capable, faster, and lower cost than Davinci.',
			'limit'			:	2049,
			'time'			:	1572480000,
			'price'			:	0.0020,
			'action'		:	[ActionCompletions],
		},
		{
			'id'			:	ModelTextBabbage1,
			'category'		:	CategoryGpt30,
			'release'		:	ReleaseCategory,
			'name'			:	'Text Babbage 1',
			'description'	:	'Fast model for straightforward tasks at lower cost.',
			'explanation'	:	'Capable of straightforward tasks, very fast, and lower cost.',
			'limit'			:	2049,
			'time'			:	1572480000,
			'price'			:	0.0005,
			'action'		:	[ActionCompletions],
		},
		{
			'id'			:	ModelTextAda1,
			'category'		:	CategoryGpt30,
			'release'		:	ReleaseCategory,
			'name'			:	'Text Ada 1',
			'description'	:	'Fastest model for simple tasks at lowest cost.',
			'explanation'	:	'Capable of very simple tasks, usually the fastest model in the GPT-3 series, and lowest cost.',
			'limit'			:	2049,
			'time'			:	1572480000,
			'price'			:	0.0004,
			'action'		:	[ActionCompletions],
		},
		{
			'id'			:	ModelDavinci,
			'category'		:	CategoryGpt30,
			'release'		:	ReleaseCategory,
			'name'			:	'Davinci',
			'description'	:	'Most capable GPT-3 model with higher quality.',
			'explanation'	:	'Most capable GPT-3 model. Can do any task the other models can do, often with higher quality.',
			'limit'			:	2049,
			'time'			:	1572480000,
			'price'			:	0.0200,
			'action'		:	[ActionCompletions],
		},
		{
			'id'			:	ModelCurie,
			'category'		:	CategoryGpt30,
			'release'		:	ReleaseCategory,
			'name'			:	'Curie',
			'description'	:	'Capable model faster and more cheaper than Davinci.',
			'explanation'	:	'Very capable, but faster and lower cost than Davinci.',
			'limit'			:	2049,
			'time'			:	1572480000,
			'price'			:	0.0020,
			'action'		:	[ActionCompletions],
		},
		{
			'id'			:	ModelBabbage,
			'category'		:	CategoryGpt30,
			'release'		:	ReleaseCategory,
			'name'			:	'Babbage',
			'description'	:	'Fast model for straightforward tasks at lower cost.',
			'explanation'	:	'Capable of straightforward tasks, very fast, and lower cost.',
			'limit'			:	2049,
			'time'			:	1572480000,
			'price'			:	0.0005,
			'action'		:	[ActionCompletions],
		},
		{
			'id'			:	ModelAda,
			'category'		:	CategoryGpt30,
			'release'		:	ReleaseCategory,
			'name'			:	'Ada',
			'description'	:	'Fastest model for simple tasks at lowest cost.',
			'explanation'	:	'Capable of very simple tasks, usually the fastest model in the GPT-3 series, and lowest cost.',
			'limit'			:	2049,
			'time'			:	1572480000,
			'price'			:	0.0004,
			'action'		:	[ActionCompletions],
		},
	]

	# https://platform.openai.com/docs/guides/error-codes/api-errors
	# https://github.com/openai/openai-python/blob/1d6142f376067e401492ca92ff88a08deb47d6ba/openai/api_requestor.py#L344
	ErrorAccountInvalid		= 'accountinvalid'		# Error: Invalid Authentication. Cause: Invalid Authentication. Solution: Ensure the correct API key and requesting organization are being used.
	ErrorAccountKey			= 'accountkey'			# Error: Incorrect API key provided. Cause: The requesting API key is not correct. Solution: Ensure the API key used is correct, clear your browser cache, or generate a new one.
	ErrorAccountMember		= 'accountmember'		# Error: You must be a member of an organization to use the API. Cause: Your account is not part of an organization. Solution: Contact us to get added to a new organization or ask your organization manager to invite you to an organization.
	ErrorAccount			= 'account'

	ErrorUsageRate			= 'usagerate'			# Error: Rate limit reached for requests. Cause: You are sending requests too quickly. Solution: Pace your requests. Read the Rate limit guide.
	ErrorUsageQuota			= 'usagequota'			# Error: You exceeded your current quota, please check your plan and billing details. Cause: You have hit your maximum monthly spend (hard limit) which you can view in the account billing section. Solution: Apply for a quota increase.
	ErrorUsageOverload		= 'usageoverload'		# Error: The engine is currently overloaded, please try again later. Cause: Our servers are experiencing high traffic. Solution: Please retry your requests after a brief wait.
	ErrorUsage				= 'usage'

	ErrorClientRequest		= 'clientrequest'
	ErrorClientPermission	= 'clientpermission'
	ErrorClientMissing		= 'clientmissing'
	ErrorClientConflict		= 'clientconflict'
	ErrorClientMedia		= 'clientmedia'

	ErrorServerProcess		= 'serverprocess'		# Error: The server had an error while processing your request. Cause: Issue on our servers. Solution: Retry your request after a brief wait and contact us if the issue persists. Check the status page.
	ErrorServer				= 'server'

	ErrorUnknown			= 'unknown'
	ErrorNone				= None

	Errors = {
		ErrorAccountInvalid		: {'code' : 401, 'expression' : r'(?:invalid|incorrect|wrong).*?auth', 'name' : 'Account Invalid', 'message' : 'The account is not authenticated.'},
		ErrorAccountKey			: {'code' : 401, 'expression' : r'(?:invalid|incorrect|wrong).*?key', 'name' : 'Account Key', 'message' : 'The account API key is invalid.'},
		ErrorAccountMember		: {'code' : 401, 'expression' : r'(?:member|organization)', 'name' : 'Account Member', 'message' : 'The request requires organizational membership.'},
		ErrorAccount			: {'code' : 401, 'expression' : None, 'name' : 'Account', 'message' : 'An unknown account error occurred.'},

		ErrorUsageRate			: {'code' : 429, 'expression' : r'rate\s*limit', 'name' : 'Usage Rate', 'message' : 'The request rate limit was reached.'},
		ErrorUsageQuota			: {'code' : 429, 'expression' : r'(?:quota|billing)', 'name' : 'Usage Quota', 'message' : 'The account quota was exceeded.'},
		ErrorUsageOverload		: {'code' : 429, 'expression' : r'overload', 'name' : 'Usage Overload', 'message' : 'The servers are currently overloaded.'},
		ErrorUsage				: {'code' : 429, 'expression' : None, 'name' : 'Usage', 'message' : 'An unknown usage error occurred.'},

		ErrorClientRequest		: {'code' : 400, 'expression' : None, 'name' : 'Client Request', 'message' : 'The request is invalid.'},
		ErrorClientPermission	: {'code' : 403, 'expression' : None, 'name' : 'Client Permission', 'message' : 'The request is not permitted.'},
		ErrorClientMissing		: {'code' : 404, 'expression' : None, 'name' : 'Client Missing', 'message' : 'The request resources are unavailable.'},
		ErrorClientConflict		: {'code' : 409, 'expression' : None, 'name' : 'Client Conflict', 'message' : 'The request has caused a conflict.'},
		ErrorClientMedia		: {'code' : 415, 'expression' : None, 'name' : 'Client Media', 'message' : 'The request media is unsupported.'},

		ErrorServerProcess		: {'code' : 500, 'expression' : r'server.*?(?:process|request)', 'name' : 'Server Process', 'message' : 'The server cannot process the request.'},
		ErrorServer				: {'code' : 500, 'expression' : None, 'name' : 'Server', 'message' : 'An unknown server error occurred.'},

		ErrorUnknown			: {'code' : 500, 'expression' : None, 'name' : 'Unknown', 'message' : 'An unknown error occurred.'},
	}

	# There are various sites that offer free ChatGPT.
	# Not sure if these sites run on top of the OpenAI API with a huge subscription, or if they have their own separate ChatGPT system.
	# Some of them have more features than others. Not all of them allow to continue a conversation (refine the chat).
	# Some of them have daily limits, some are unlimited.
	# With some of them it is not clear which model they use.
	# The official OpenAI interface (https://chat.openai.com/chat) is Cloudflare protected and requires a session cookie (login required). Using the offcial API is better in this case.
	PlaygroundOrggpt			= 'orggpt'
	PlaygroundProxygpt			= 'proxygpt'
	PlaygroundYqcloudgpt		= 'yqcloudgpt'
	PlaygroundFastgpt			= 'fastgpt'
	PlaygroundUnligpt			= 'unligpt'
	PlaygroundAitianhugpt		= 'aitianhugpt'
	PlaygroundAianswergpt		= 'aianswergpt'
	PlaygroundAiaskgpt			= 'aiaskgpt'
	PlaygroundAutomatic			= True
	PlaygroundDisabled			= False

	# Features: True = full support, None = partial support, False = no support.
	# NB: Order matters here. Put the best and most reliable playgrounds first. The less relibale they are, the further down the list they shoiuld be palced.
	# NB: Should also correspond with the order in the settings. Used by settingsPlaygroundEnable().
	# Playgrounds:
	#	https://www.elegantthemes.com/blog/business/best-chatgpt-alternatives
	#	https://github.com/LiLittleCat/awesome-free-chatgpt/blob/main/README_en.md
	#	https://ai-pig-fly.space/home
	#		https://bettergpt.chat							- Invalid API key or no credits.
	#		https://freechatgpt.chat						- Invalid API key or no credits.
	#		https://chat.pawan.krd							- Strong Cloudflare protection.
	#		https://freegpt.one								- Strong Cloudflare protection.
	#		https://ora.sh/openai/gpt4						- Now requires login.
	#		https://huggingface.co/spaces/ysharma/ChatGPT4	- Just returns errors.
	#		https://chatbot.theb.ai							- Strong Cloudflare protection.
	#		https://chat.gpt.bz								- Basic code-based captcha.
	#		https://chat.gptplus.one						- Uses a JS-calculated AES-encrypted secret in API calls.
	#		http://chat.cutim.one							- Uses a JS-calculated AES-encrypted secret in API calls.
	#		https://chat.waixingyun.cn						- Does not return a valid reponse.
	#		https://www.nav4ai.com/chatgpt					- Invalid API key.
	#		https://www.promptboom.com						- Uses some JS secret in API calls.
	#		https://x1.xjai.cc								- Just loads, does not provide a response.
	#		https://bettergpt.chat							- Invalid API key or quota reached.
	#		https://freechatgpt.chat							- Invalid API key or quota reached.
	Playgrounds					= [
		{
			'id'				: PlaygroundOrggpt,
			'name'				: 'OrgGPT',
			'description'		: 'A partly customizable {name} API using its own internal {organization} key. The API is relatively reliable and seems to rarely reach its quotas.',
			'link'				: {'web' : 'https://chat-gpt.org', 'api' : 'https://chat-gpt.org/api/text'},
			'feature'			: {'reliable' : True, 'category' : [CategoryGpt30], 'model' : None, 'refine' : False, 'parameters' : True},
		},
		{
			'id'				: PlaygroundProxygpt,
			'name'				: 'ProxyGPT',
			'description'		: 'A uncustomizable {name} API using its own internal {organization} key. The API is relatively reliable and seems to rarely reach its quotas.',
			'link'				: {'web' : 'https://chatgptproxy.me', 'api' : ['https://chatgptproxy.me/api/v1/chat/conversation', 'https://chatgptproxy.me/api/v1/chat/result']},
			'feature'			: {'reliable' : True, 'category' : [CategoryGpt30], 'model' : None, 'refine' : True, 'parameters' : False},
		},
		{
			'id'				: PlaygroundYqcloudgpt,
			'name'				: 'YqCloudGPT',
			'description'		: 'A uncustomizable {name} API using its own internal {organization} key. The API is relatively reliable and seems to rarely reach its quotas.',
			'link'				: {'web' : 'https://dev.yqcloud.top', 'api' : ['https://api.aichatos.cloud/api/generateStream']},
			'feature'			: {'reliable' : False, 'category' : [CategoryGpt30], 'model' : None, 'refine' : True, 'parameters' : False},
		},
		{
			'id'				: PlaygroundFastgpt,
			'name'				: 'FastGPT',
			'description'		: 'A uncustomizable {name} API using its own internal {organization} key. The API is relatively reliable and seems to often reach its quotas.',
			'link'				: {'web' : 'https://fastgpt.app', 'api' : ['https://fastgpt.app/backend-api/conversation']},
			'feature'			: {'reliable' : False, 'category' : [CategoryGpt30, CategoryGpt35, CategoryGpt40], 'model' : None, 'refine' : True, 'parameters' : True},
		},
		{
			'id'				: PlaygroundUnligpt,
			'name'				: 'UnliGPT',
			'description'		: 'A uncustomizable {name} API using its own internal {organization} key. The API is relatively reliable and seems to sometimes reach its quotas.',
			'link'				: {'web' : 'https://chatgptunli.com/chatgpt', 'api' : ['https://www.chatgptunli.com/wp-json/mwai-ui/v1/chats/submit']}, # API link must contain www subdomain.
			'feature'			: {'reliable' : False, 'category' : [CategoryGpt30], 'model' : None, 'refine' : True, 'parameters' : False},
		},
		{
			'id'				: PlaygroundAitianhugpt,
			'name'				: 'AiTianhuGPT',
			'description'		: 'A uncustomizable {name} API using its own internal {organization} key. The API is relatively unreliable and seems to often reach its quotas.',
			'link'				: {'web' : 'https://www.aitianhu.com', 'api' : ['https://www.aitianhu.com/api/chat-process']}, # Must use www.
			'feature'			: {'reliable' : False, 'category' : [CategoryGpt30], 'model' : None, 'refine' : True, 'parameters' : False},
		},
		{
			'id'				: PlaygroundAianswergpt,
			'name'				: 'AiAnswerGPT',
			'description'		: 'A uncustomizable {name} API using its own internal {organization} key. The API is relatively reliable and seems to sometimes reach its quotas.',
			'link'				: {'web' : 'https://aiknow.me', 'api' : ['https://a.aianswer.me']},
			'feature'			: {'reliable' : False, 'category' : [CategoryGpt35], 'model' : None, 'refine' : False, 'parameters' : False}, # Has an option to use ChatGPT4, but always throws an error.
		},
		{
			'id'				: PlaygroundAiaskgpt,
			'name'				: 'AiAskGPT',
			'description'		: 'A uncustomizable {name} API using its own internal {organization} key. The API is relatively reliable and seems to sometimes reach its quotas.',
			'link'				: {'web' : 'https://chat.aiask.me', 'api' : ['https://chat.aiask.me/v1/chat/gpt/']},
			'feature'			: {'reliable' : False, 'category' : [CategoryGpt35], 'model' : None, 'refine' : True, 'parameters' : None}, # Has ChatGpt4.0 support, but that requires a custom key.
		},
	]

	OutputText					= 'text'		# Chatbot replies with single body of text.
	OutputTextStream			= 'textstream'	# Chatbot replies with multiple lines of text, from which the last line should be used.
	OutputJson					= 'json'		# Chatbot replies with single body of JSON.
	OutputJsonStream			= 'jsonstream'	# Chatbot replies with multiple lines of JSON, from which the last line should be used.
	OutputDefault				= OutputJson

	SettingsPlayground			= 'oracle.%s.playground'
	SettingsPlaygroundAccess	= 'oracle.%s.playground.access' # Not in settings.xml, only in settings.db.
	SettingsModel				= 'oracle.%s.model'
	SettingsModelLimit			= 'oracle.%s.model.limit'
	SettingsModelRandomness		= 'oracle.%s.model.randomness'
	SettingsModelCreativity		= 'oracle.%s.model.creativity'

	# https://platform.openai.com/tokenizer
	# One token generally corresponds to ~4 characters of text for common English text.
	# 1,000 tokens is about 750 words.
	# In reality "list new amazon prime shows" is 12 tokens (maybe the entire JSON message obbject is used).
	TokenRatio				= 3.0		# Make smaller than needed to accomodate discrepancies.
	TokenQuery				= 500		# Upper limit of tokens used per query. Used to estimate prices. In reality it is closer to 150-250 tokens per query, but we also accomodate guided questions.
	TokenDefault			= 1000		# Maximum number of tokens to use by default if the settings is "Automatic".

	RetryCount				= 1
	RetryDelay				= 3

	Timeout					= 90		# The number of seconds for each 500 tokens (1 standard query). Use higher request timeout, since ChatGPT can sometimes take very long to reply, especially for larger lists. 60 seconds is in some cases too little if 20 IDs in JSON are rertrieved (probably only if the servers are overloaded).

	Separator				= '\n\n'	# The separator used by the chatbot to distinguish between messages in a conversation.

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		Oracle.__init__(self,
			id				= 'chatgpt',
			name			= 'ChatGPT',
			organization	= 'OpenAI',

			type			= Oracle.TypeChatbot,
			subscription	= [Oracle.SubscriptionFree, Oracle.SubscriptionPaid],
			intelligence	= Oracle.IntelligenceHigh,
			rating			= 5,
			color			= 'FF10A37F',

			linkWeb			= 'https://openai.com',
			linkApi			= 'https://api.openai.com/v1/',
			linkAccount		= 'https://platform.openai.com',
			linkKey			= 'https://platform.openai.com/account/api-keys',
			linkPrices		= 'https://openai.com/pricing',

			# ChatGPT returns 50-90% incorrect TMDb IDs (eg: when searching sets).
			# The IMDb IDs are mostly correct, with a few exceptions (eg: Avatar 2 which might be due to outdated training data).
			# In some rare cases, 50-90% of the IMDb IDs returned are also incorrect. Only noticed this with playgrounds, which might use even more outdated data and use older models (eg: ChatGPT3.0).
			# Disable ID searches for sets, but leave the rest enabled.
			# Update: Many IMDb IDs are also wrong if the search is very narrow, like searching for Korean/Japanese shows.
			# Disable all ID searches for now and only search by title.
			querySupport	= {
				Media.Mixed					: {
					Oracle.ModePlain		: True,
					Oracle.ModeList			: True,
					Oracle.ModeSingle		: True,

					Oracle.QueryContext		: True,
					Oracle.QueryRaw			: True,
					Oracle.QueryTextTitle	: True,
					Oracle.QueryTextId		: False,
					Oracle.QueryJsonTitle	: True,
					Oracle.QueryJsonId		: False,
				},
				Media.Movie					: {
					Oracle.ModePlain		: True,
					Oracle.ModeList			: True,
					Oracle.ModeSingle		: True,

					Oracle.QueryContext		: True,
					Oracle.QueryRaw			: True,
					Oracle.QueryTextTitle	: True,
					Oracle.QueryTextId		: False,
					Oracle.QueryJsonTitle	: True,
					Oracle.QueryJsonId		: False,
				},
				Media.Set					: {
					Oracle.ModePlain		: True,
					Oracle.ModeList			: True,
					Oracle.ModeSingle		: True,

					Oracle.QueryContext		: True,
					Oracle.QueryRaw			: True,
					Oracle.QueryTextTitle	: True,
					Oracle.QueryTextId		: False,
					Oracle.QueryJsonTitle	: True,
					Oracle.QueryJsonId		: False,
				},
				Media.Show					: {
					Oracle.ModePlain		: True,
					Oracle.ModeList			: True,
					Oracle.ModeSingle		: True,

					Oracle.QueryContext		: True,
					Oracle.QueryRaw			: True,
					Oracle.QueryTextTitle	: True,
					Oracle.QueryTextId		: False,
					Oracle.QueryJsonTitle	: True,
					Oracle.QueryJsonId		: False,
				},
			},
		)

	##############################################################################
	# SETTINGS - PLAYGROUND
	##############################################################################

	def settingsPlayground(self, label = False):
		playground = Settings.getString(self._settingsFormat(id = Chatgpt.SettingsPlayground))
		if label: return playground
		else: return self._playground(playground = playground)

	def settingsPlaygroundEnabled(self):
		return not self.settingsPlaygroundDisabled()

	def settingsPlaygroundDisabled(self):
		return self.settingsPlayground() == Chatgpt.PlaygroundDisabled

	def settingsPlaygroundEnable(self, playground = PlaygroundAutomatic):
		self.settingsPlaygroundSet(playground = playground)

	def settingsPlaygroundDisable(self):
		self.settingsPlaygroundSet(playground = Chatgpt.PlaygroundDisabled)

	def settingsPlaygroundSet(self, playground):
		Settings.set(self._settingsFormat(id = Chatgpt.SettingsPlayground), self._playgroundLabel(playground))

	def settingsPlaygroundDialog(self, settings = False):
		current = self.settingsPlayground(label = True)

		items = [
			{'title' : Dialog.prefixBack(33486), 'close' : True},
			{'title' : Dialog.prefixNext(33239), 'action' : self.helpPlayground},
			{'title' : Dialog.prefixNext(33564), 'close' : True, 'return' : True},
			{'title' : 32310, 'items' : [
				{
					'title' : Translation.string(32302),
					'value' : Translation.string(33769),
					'close' : True,
					'return' : Chatgpt.PlaygroundDisabled,
					'selection' : self._playgroundLabel(playground = Chatgpt.PlaygroundDisabled) == current,
				},
				{
					'title' : Translation.string(33800),
					'value' : Translation.string(33770),
					'close' : True,
					'return' : Chatgpt.PlaygroundAutomatic,
					'selection' : self._playgroundLabel(playground = Chatgpt.PlaygroundAutomatic) == current,
				},
			]}
		]

		playgrounds = []
		for playground in Chatgpt.Playgrounds:
			playgrounds.append({
				'title' : playground['name'],
				'value' : playground['link']['web'],
				'close' : True,
				'return' : playground,
				'selection' : self._playgroundLabel(playground = playground) == current,
			})
		items.append({'title' : 33846, 'items' : playgrounds})

		choice = Dialog.information(title = 33844, items = items, reselect = Dialog.ReselectYes)
		if not choice is None: self.settingsPlaygroundSet(playground = choice)

		if settings: Settings.launch(id = self._settingsFormat(id = Chatgpt.SettingsPlayground))

	def settingsPlaygroundAccess(self):
		return Settings.getData(self._settingsFormat(id = Chatgpt.SettingsPlaygroundAccess), verify = False)

	def settingsPlaygroundAccessSet(self, data):
		Settings.setData(self._settingsFormat(id = Chatgpt.SettingsPlaygroundAccess), data)

	##############################################################################
	# SETTINGS - MODEL
	##############################################################################

	def settingsModel(self, label = False):
		model = Settings.getString(self._settingsFormat(id = Chatgpt.SettingsModel))
		if label: return model
		else: return self._model(model = model)

	def settingsModelDialog(self, settings = False):
		id = self._settingsFormat(id = Chatgpt.SettingsModel)
		current = self.settingsModel(label = True)

		items = [
			{'title' : Dialog.prefixBack(33486), 'close' : True},
			{'title' : Dialog.prefixNext(33239), 'action' : self.helpModel},
			{'title' : Dialog.prefixNext(33564), 'close' : True, 'return' : True},
		]

		categories = {}
		for model in Chatgpt.Models:
			category = model['category']
			if not category in categories: categories[category] = []

			value = [
				'%s %s' % (Math.thousand(model['limit']), Translation.string(32311)),
				'%s $%.4f' % (Font.icon(Font.IconEstimator), model['price'] / (1000.0 / Chatgpt.TokenQuery)), # Per query.
				ConverterTime(model['time']).string(format = ConverterTime.FormatMonthShort, offset = ConverterTime.OffsetUtc),
			]

			categories[category].append({
				'title' : model['name'],
				'value' : Format.iconJoin(value),
				'close' : True,
				'return' : model,
				'selection' : self._modelLabel(model = model) == current,
			})

		for category, models in categories.items():
			items.append({'title' : self._categoryLabel(category = category, release = True), 'items' : models})

		choice = Dialog.information(title = 33816, items = items, reselect = Dialog.ReselectYes)

		if choice is True: Settings.set(id, Translation.string(33800))
		elif choice: Settings.set(id, self._modelLabel(model = choice))

		if settings: Settings.launch(id = id)

	def settingsModelLimit(self, default = True):
		result = Settings.getCustom(self._settingsFormat(id = Chatgpt.SettingsModelLimit))
		if default and result is None: result = Chatgpt.TokenDefault
		return result

	def settingsModelRandomness(self, scale = True):
		result = Settings.getInteger(self._settingsFormat(id = Chatgpt.SettingsModelRandomness))
		if scale: result = self._scaleRandomness(result)
		return result

	def settingsModelCreativity(self, scale = True):
		result = Settings.getInteger(self._settingsFormat(id = Chatgpt.SettingsModelCreativity))
		if scale: result = self._scaleCreativity(result)
		return result

	##############################################################################
	# HELP
	##############################################################################

	def helpDescription(self, details = False, account = False):
		help = '%s is a generic AI chatbot developed by %s that assists with human-language searches.' % (self.name(), self.organization())
		if details: help += ' It is an intelligent chatbot with advanced capabilities.'
		if account: help += ' Free and paid accounts are available.'
		return help

	def helpAuthentication(self, dialog = True):
		name = self.name()
		organization = self.organization()

		items = [
			{'type' : 'title', 'value' : 'Chatbot'},
			{'type' : 'text', 'value' : self.helpDescription(details = True, account = True)},

			{'type' : 'title', 'value' : 'Characteristics'},
			{'type' : 'text', 'value' : '%s has the following characteristics:' % (name)},
			{'type' : 'subtitle', 'value' : 'Advantages'},
			{'type' : 'list', 'number' : False, 'value' : [
				{'value' : 'State of the art chatbot with good intelligence.'},
				{'value' : 'Variety of customizable models.'},
				{'value' : 'Quick response time.'},
				{'value' : 'Free accounts and low prices for paid subscriptions.'},
			]},
			{'type' : 'subtitle', 'value' : 'Disadvantages'},
			{'type' : 'list', 'number' : False, 'value' : [
				{'value' : 'Only data up to September 2021 for older models.'},
				{'value' : 'No integrated search engine.'},
				{'value' : 'Subjective replies are occasionally censored.'},
				{'value' : 'Limited trial accounts with expiration date.'},
			]},

			{'type' : 'title', 'value' : 'Accounts'},
			{'type' : 'text', 'value' : 'An %s account is needed in order to use %s. Account registration requires you to verify your email address and phone number. Some countries are blocked. After registration you are awarded $5 worth of tokens, which should be enough for 5000 queries. Note that the free grant expires after 3 to 4 months, after which a paid subscription is required. Accounts can be registered here:' % (organization, name)},
			{'type' : 'link', 'value' : self.linkAccount()},

			{'type' : 'title', 'value' : 'Usage'},
			{'type' : 'text', 'value' : '%s uses tokens to control their API usage. For each word in the chat conversation you will be deducted a certain number of tokens. This includes your own questions and the answers given by the chatbot.' % (organization)},
			{'type' : 'text', 'value' : '%s specifies that [B]100[/B] tokens are approximately [B]75[/B] words. The average word length in English is about [B]4[/B] characters and is a better estimation of the tokens that will be consumed. For instance, if the total length of the chat is 400 characters, including spaces and symbols, approximately 100 tokens will be used. This approximation will vary with other languages that might have a different average word length.' % (organization)},
			{'type' : 'text', 'value' : 'With the default settings, a chat should consume an average of around [B]500[/B] tokens, considering the length of the answer and the refined or guided queries discussed below. This is an overestimate and, in most cases, you will probably only use around 150 to 250 tokens per chat.'},
			{'type' : 'text', 'value' : 'Note that different models have different pricing. For newer and better models you will pay more than for older and inferior models. The full pricing can be found here:'},
			{'type' : 'link', 'value' : self.linkPrices()},
		]

		items.extend(self.helpPlayground(dialog = False, details = False))

		if dialog: self.helpDialog(items = items)
		return items

	def helpPlayground(self, dialog = True, details = True):
		name = self.name()
		organization = self.organization()

		items = [
			{'type' : 'title', 'value' : 'Playgrounds'},
			{'type' : 'text', 'value' : 'Since %s moved from a free to a paid subscription model, many community projects have started to provide free access to %s. These free community projects are referred to as [I]playgrounds[/I]. Playgrounds do not require an account, but might imposed their own daily limits, although many of them have no usage restrictions at all. Most playgrounds only provide access to older %s models with limited parameter customizability.' % (organization, name, name)},
			{'type' : 'text', 'value' : 'Note that although playgrounds are free, they are very [B]unreliable[/B] and might get shut down at any moment. Playgrounds have their own %s API keys or use API keys provided by community members, which might get restricted by %s in the future. You can try to use a playground, but if unsuccessful, you might have to create your own free %s account.' % (organization, organization, organization)},
		]

		if details: items.append(	{'type' : 'text', 'value' : 'The [I]Disabled[/I]  option will completely disable the utilization of any free playground. The [I]Automatic[/I]  option will sequentially try one playground after the other until a working one was found.'})

		playgrounds = []
		for playground in Chatgpt.Playgrounds:
			link = playground['link']['web'][0] if Tools.isArray(playground['link']['web']) else playground['link']['web']
			reliable = 'Relatively %s' % ('Reliable' if playground['feature']['reliable'] else 'Unreliable')
			category = Format.iconJoin([self._categoryLabel(i) for i in playground['feature']['category']])

			if details:
				items.append({'type' : 'subtitle', 'value' : playground['name']})
				items.append({'type' : 'text', 'value' : playground['description'].format(**{'name' : name, 'organization' : organization})})
				items.append({'type' : 'list', 'number' : False, 'value' : [
					{'title' : 'Web Link', 'link' : link},
					{'title' : 'Reliable Access', 'value' : reliable},
					{'title' : 'Supported Models', 'value' : category},
					{'title' : 'Customize Models', 'value' : Translation.string(33341 if playground['feature']['parameters'] else 33342)},
					{'title' : 'Chat Refinement', 'value' : Translation.string(33341 if playground['feature']['refine'] else 33342)},
				]})
			else:
				playgrounds.append({'title' : playground['name'], 'value' : Format.iconJoin([reliable, category]), 'link' : link})

		if not details: items.append({'type' : 'list', 'number' : False, 'value' : playgrounds})

		if dialog: self.helpDialog(items = items)
		return items

	def helpModel(self, dialog = True):
		name = self.name()
		organization = self.organization()

		items = [
			{'type' : 'title', 'value' : 'Models'},
			{'type' : 'text', 'value' : 'Various models can be used with ChatGPT. Models have different capabilities and are trained differently, which can result in distinct replies. Models also have different output limits with varying costs. Models are trained with data sets containing samples up to a specific date.'},
			{'type' : 'text', 'value' : 'The default [I]%s[/I]  option will utilize %s.' % (Translation.string(33800), self._modelLabel(model = Chatgpt.ModelDefault))},
		]

		for model in Chatgpt.Models:
			items.extend([
				{'type' : 'subtitle', 'value' : self._modelLabel(model)},
				{'type' : 'text', 'value' : model['explanation']},
				{'type' : 'list', 'number' : False, 'value' : [
					{'title' : 'Query Limit', 'value' : '%s tokens' % Math.thousand(model['limit'])},
					{'title' : 'Query Price', 'value' : Format.iconJoin(['%s $%.4f per query' % (Font.icon(Font.IconEstimator), model['price'] / (1000.0 / Chatgpt.TokenQuery)), '$%.4f per 1000 tokens' % model['price']])},
					{'title' : 'Training Data', 'value' : 'Up to %s' % ConverterTime(model['time']).string(format = ConverterTime.FormatMonth, offset = ConverterTime.OffsetUtc)},
					{'title' : 'Model Release', 'value' : self._releaseLabel(release = model['release'], category = model['category'], description = True)},
				]},
			])

		if dialog: self.helpDialog(items = items)
		return items

	##############################################################################
	# ACCOUNT
	##############################################################################

	def account(self):
		return Account.instance()

	def accountKey(self):
		return self.account().dataKey()

	def accountAuthenticated(self, free = False):
		if self.account().authenticated(): return True
		elif free: return self.settingsPlaygroundEnabled()
		else: return False

	def accountAuthentication(self, settings = False):
		return self.account().authenticate(settings = settings)

	def accountVerification(self, key = None):
		result = self._requestOpenai(action = 'models', cache = False, retry = False, key = key)
		return bool(result and result['success'])

	##############################################################################
	# INTERNAL
	##############################################################################

	def _tokens(self, data):
		return Math.roundUp(float(len(Converter.jsonTo(data))) / Chatgpt.TokenRatio)

	def _scale(self, value, fromMinimum = None, fromMaximum = None, toMinimum = -2.0, toMaximum = 2.0):
		if fromMinimum is None: fromMinimum = 0.0
		if fromMaximum is None: fromMaximum = 1.0 if (Tools.isFloat(value) and value >= 0.0 and value <= 1.0) else 100.0
		return Math.scale(value = value, fromMinimum = fromMinimum, fromMaximum = fromMaximum, toMinimum = toMinimum, toMaximum = toMaximum)

	def _scaleRandomness(self, value):
		return self._scale(value = value, fromMinimum = None, fromMaximum = None, toMinimum = 0.0, toMaximum = 2.0)

	def _scaleCreativity(self, value):
		return self._scale(value = value, fromMinimum = None, fromMaximum = None, toMinimum = -2.0, toMaximum = 2.0)

	def _translate(self, data):
		if Tools.isString(data):
			extract = Regex.extract(data = data, expression = r'\$ADDON\[.*\s(\d+)\]')
			if extract: data = Translation.string(int(extract))
		return data

	##############################################################################
	# INTERNAL - RELEASE
	##############################################################################

	def _release(self, release, category = None, details = False):
		try:
			if release:
				if Tools.isDictionary(release):
					return release if details else release['id']
				else:
					release = release.lower()
					if release == Chatgpt.ReleaseCategory:
						try: release = self._category(category = category, details = True)['release']
						except: release = None
					if release:
						for i in Chatgpt.Releases:
							if release == i['id'] or release == i['name'].lower():
								return i if details else i['id']
		except: Logger.error()
		return None

	def _releaseLabel(self, release, category = None, description = False):
		release = self._release(release = release, category = category, details = True)
		if description and release:
			description = release['description'].strip('.')
			description = description[0].lower() + description[1:]
			return '%s (%s)' % (release['name'], description)
		elif release: return release['name']
		return None

	def _releaseDescription(self, release, category = None):
		release = self._release(release = release, category = category, details = True)
		if release: return release['description']
		return None

	##############################################################################
	# INTERNAL - CATEGORY
	##############################################################################

	def _category(self, category, details = False):
		try:
			if category:
				if Tools.isDictionary(category):
					return category if details else category['id']
				else:
					category = category.lower()
					for i in Chatgpt.Categories:
						if category == i['id'] or category == i['name'].lower():
							return i if details else i['id']
		except: Logger.error()
		return None

	def _categoryLabel(self, category, release = False):
		category = self._category(category = category, details = True)
		if category and release: return '%s (%s)' % (category['name'], self._releaseLabel(release = category['release'], description = False))
		elif category: return category['name']
		return None

	def _categoryDescription(self, category):
		category = self._category(category = category, details = True)
		if category: return category['description']
		return None

	##############################################################################
	# INTERNAL - MODEL
	##############################################################################

	def _model(self, model, details = False, default = True):
		try:
			model = self._translate(model) # Default setting: $ADDON[plugin.video.gaia 33800]
			if model is True or model is None or model == Translation.string(33800): model = Chatgpt.ModelDefault

			if model:
				if Tools.isDictionary(model):
					return model if details else model['id']
				else:
					model = model.lower()
					for i in Chatgpt.Models:
						if model == i['id'] or model == self._modelLabel(model = i).lower():
							return i if details else i['id']
		except: Logger.error()

		# If a user selected a specific model, but it was later removed from ChatGPT and the settings
		return self._model(model = Chatgpt.ModelDefault, details = details, default = False) if default else None

	def _modelLabel(self, model, category = True):
		model = self._model(model = model, details = True)
		if category: category = self._categoryLabel(category = model['category'])
		if model and category: return '%s (%s)' % (category, model['name'])
		elif model: return model['name']
		else: return None

	def _modelDescription(self, model):
		model = self._playground(model = model, details = True)
		if model: return model['description']
		return None

	##############################################################################
	# INTERNAL - PLAYGROUND
	##############################################################################

	def _playground(self, playground, details = False, default = True):
		try:
			playground = self._translate(playground) # Default setting: $ADDON[plugin.video.gaia 32302]

			if playground is True or playground is None or playground == Translation.string(33800):
				if details: return {'id' : Chatgpt.PlaygroundAutomatic, 'name' : Translation.string(33800), 'category' : None}
				else: return Chatgpt.PlaygroundAutomatic
			elif playground is False or playground == Translation.string(32302):
				if details: return {'id' : Chatgpt.PlaygroundDisabled, 'name' : Translation.string(32302), 'category' : None}
				else: return Chatgpt.PlaygroundDisabled

			if Tools.isDictionary(playground):
				return playground if details else playground['id']
			else:
				playground = playground.lower()
				for i in Chatgpt.Playgrounds:
					if playground == i['id'] or playground == self._playgroundLabel(playground = i):
						return i if details else i['id']
		except: Logger.error()

		# If a user selected a specific playground, but it was later removed from ChatGPT and the settings
		return self._playground(playground = Chatgpt.PlaygroundAutomatic, details = details, default = False) if default else None

	def _playgroundLabel(self, playground):
		playground = self._playground(playground = playground, details = True)
		if playground: return playground['name']
		else: return None

	def _playgroundDescription(self, playground):
		playground = self._playground(playground = playground, details = True)
		if playground: return playground['description']
		return None

	##############################################################################
	# CHAT
	##############################################################################

	def _chat(self, message, context = None, conversation = None, refine = None, media = None):
		model = self.settingsModel()
		limit = self.settingsModelLimit()
		creativity = self.settingsModelCreativity(scale = False)
		randomness = self.settingsModelRandomness(scale = False)

		result = None
		if self.accountAuthenticated(): result = self._requestChatgpt(message = message, context = context, conversation = conversation, refine = refine, model = model, limit = limit, randomness = randomness, creativity = creativity)

		try: last = result['chat']['history'][-1]['data']
		except: last = None
		if not result or (result['error'] and (not last or (Tools.isDictionary(last) and 'error' in last))):
			result2 = self._requestPlayground(message = message, context = context, conversation = conversation, refine = refine, model = model, limit = limit, randomness = randomness, creativity = creativity)
			if result2: result = result2

		return result

	##############################################################################
	# REQUEST
	##############################################################################

	def _request(self, link, data = None, headers = None, cookies = None, playground = None, cache = False, retry = True, notification = True, output = OutputDefault):
		# Manually measure time, since networker.responseDurationRequest() can return None if the request was aborted by the server.
		timer = Time(start = True)

		timeout = int(min(Chatgpt.Timeout * 3, max(Chatgpt.Timeout, Chatgpt.Timeout * (self._tokens(data) / 500.0)))) if data else None
		networker = Networker()

		response = networker.request(type = Networker.DataJson, link = link, data = data, headers = headers, cookies = cookies, cache = cache, timeout = timeout)

		# Sometimes ChatGPT takes a very long time respond and then aborts the connection without returning any data:
		#	('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
		# When the same request is submitted a few seconds later, ChatGPT replies very quickly with the correct data.
		# Not sure what causes this, but maybe if the query is too nuance or requires too much computation, ChatGPT realizes that it won't be able to reply within a given time period, and then just drops the connection.
		# The query is still continued in the background, so when a 2nd query is made, ChatGPT can reply with the cached answer.
		if retry:
			if retry is True: retry = Chatgpt.RetryCount
			while retry > 0 and response and response['error']['type'] == Networker.ErrorConnection:
				Logger.log('ChatGPT aborted the connection. Retrying query: %s' % Converter.jsonTo(data), type = Logger.TypeError)
				Time.sleep(Chatgpt.RetryDelay)
				retry -= 1
				response = networker.request(method = Networker.MethodPost, type = Networker.DataJson, link = link, data = data, headers = headers, cookies = cookies, cache = cache, timeout = timeout)

		data = networker.responseDataText()
		if output and not Tools.isArray(output): output = [output]
		for o in output:
			if o == Chatgpt.OutputTextStream or o == Chatgpt.OutputJsonStream:
				try:
					data = Converter.unicode(data)
					data = data.split('\n')
					data = data[-1]
					if o == Chatgpt.OutputJsonStream: data = Converter.jsonFrom(data)
				except:
					Logger.error()
					data = None
			elif o == Chatgpt.OutputText:
				pass
			elif o == Chatgpt.OutputJson:
				data = Converter.jsonFrom(data)
			elif Tools.isFunction(o):
				data = o(data)
			elif Tools.isString(o):
				extract = Regex.extract(data = data or '', expression = o, flags = Regex.FlagCaseInsensitive | Regex.FlagAllLines)
				data = extract if extract else None

		error = self._requestError(code = response['error']['code'], data = data, playground = playground, notification = notification)

		return {
			'success' : bool(data and not error),
			'error' : error,
			'duration' : timer.elapsed(milliseconds = True),
			'data' : data,
		}

	def _requestCookies(self, link, data = None, headers = None, cookies = None):
		return Networker().requestCookies(link = link, data = data, headers = headers, cookies = cookies)

	def _requestOpenai(self, action, data = None, cache = None, retry = False, key = None, notification = True):
		if key is None: key = self.accountKey()

		if Tools.isList(action): link = Networker.linkJoin(self.linkApi(), *action)
		else: link = Networker.linkJoin(self.linkApi(), action)

		headers = {Networker.HeaderAuthorization: '%s %s' % (Networker.AuthorizationBearer, key)}
		return self._request(link = link, data = data, headers = headers, cache = cache, retry = retry, notification = notification)

	def _requestError(self, code = None, data = None, type = None, playground = None, notification = False):
		result = Chatgpt.ErrorNone

		if type:
			error = Chatgpt.Errors[type]
			result = {'type' : type, 'name' : error['name'], 'message' : error['message'], 'description' : None}
		else:
			try: message = '' if data['error']['message'] is None else data['error']['message']
			except:
				try: message = '' if data['error'] is None else str(data['error'])
				except: message = ''

			# PlaygroundAitianhugpt
			# Eg: data = "ChatGPT error 429: {"detail":"rate limited."}"
			if data and not message:
				try:
					error = Regex.extract(data = str(data), expression = r'error.*?[^\da-z]([2-5]\d{2})[^\da-z]')
					if error:
						message = str(data)
						code = int(error)
				except: Logger.error()

			if not result:
				if code:
					for type, error in Chatgpt.Errors.items():
						if code == error['code'] and (error['expression'] is None or Regex.match(data = message, expression = error['expression'])):
							result = {'type' : type, 'name' : error['name'], 'message' : error['message'], 'description' : message if message else None}
							break
				elif message:
					for type, error in Chatgpt.Errors.items():
						if error['expression'] and Regex.match(data = message, expression = error['expression']):
							result = {'type' : type, 'name' : error['name'], 'message' : error['message'], 'description' : message if message else None}
							break
					if result is Chatgpt.ErrorNone:
						error = Chatgpt.Errors[Chatgpt.ErrorUnknown]
						result = {'type' : Chatgpt.ErrorUnknown, 'name' : error['name'], 'message' : error['message'], 'description' : message if message else None}

		if notification and result:
			title = [self.name()]
			if playground: title.append(playground['name'])
			Dialog.notification(title = Format.iconJoin(title), message = result['message'], icon = Dialog.IconWarning)

		return result

	##############################################################################
	# REQUEST - CHATGPT
	##############################################################################

	def _requestChatgpt(self, message, context = None, conversation = None, refine = False, model = None, limit = None, randomness = None, creativity = None, retry = True):
		result = None
		try:
			timer = Time(start = True)
			time1 = Time.timestamp()

			result = self._result()
			result['error'] = self._requestError(type = Chatgpt.ErrorServer)
			model = self._model(model = model, details = True, default = True)
			category = self._category(category = model['category'], details = True)

			if refine and category['refine']: refine = self._chatRefine(conversation)
			else: refine = None

			history = conversation['chat']['history'] if conversation else []
			if history: id = history[-1]['id'] + (0 if refine else 1)
			else: id = 1

			refined = []
			if model['action'][0] == Chatgpt.ActionCompletions:
				attribute = 'prompt'
				query = [message]

				# An array of messages can be passed in as the "prompt" parameter, but it is not seen as a sequence of chats.
				# Rather, the array is seen as separate questions, and the response will contain an answer for each input prompt.
				# Instead, combined the previous questions + answers into one long string.
				if refine: query = refine + query

				refined = query
				query = Chatgpt.Separator.join(query)
			else:
				attribute = 'messages'
				query = [{'role' : 'user', 'content' : message}]
				if refine: query = refine + query
				elif context and (not history or not refine): query.insert(0, {'role' : 'system', 'content' : context[0] if Tools.isArray(context) else context})
				refined = query

			tokens = self._tokens(query)
			if not limit: limit = self.settingsModelLimit()
			limit = min(model['limit'] - tokens, limit)

			if randomness is None: randomness = self.settingsModelRandomness(scale = False)
			if creativity is None: creativity = self.settingsModelCreativity(scale = False)

			Tools.update(result['chatbot'], {
				'model' : model['id'],
				'category' : model['category'],
				'limit': limit,
				'randomness' : randomness / 100.0,
				'creativity' : creativity / 100.0,
			})

			randomness = self._scaleRandomness(randomness)
			creativity = self._scaleCreativity(creativity)

			data = {
				'model' : model['id'],
				'max_tokens' : limit,
				'temperature' : randomness,
				'presence_penalty' : creativity,
				'stream' : False,
				attribute : query,
			}

			returned = self._requestOpenai(action = model['action'], data = data, retry = retry)
			time2 = Time.timestamp()

			if returned:
				try: response = returned['data']['choices'][0]['message']['content']
				except:
					try: response = returned['data']['choices'][0]['text']
					except: response = None

				if category['refine'] and returned['data'] and 'choices' in returned['data'] and returned['data']['choices']: refined = refined + [i['message'] if 'message' in i else i['text'] for i in returned['data']['choices']]
				else: refined = None

				Tools.update(result, {
					'success' : bool(returned['success'] and response),
					'error' : returned['error'],
					'chat' : {'refine' : refined},
				})

				try: result['duration'] = conversation['duration']
				except: pass
				result['duration'] = (result['duration'] or 0) + max(timer.elapsed(milliseconds = True), returned['duration'] or 0) # Get the max in case a cached result was returned.

				tokens = {}
				for key1, key2 in {'used' : 'total_tokens', 'request' : 'prompt_tokens', 'response' : 'completion_tokens'}.items():
					try:
						token = returned['data']['usage'][key2]
						tokens[key1] = token
						try: result['usage']['token'][key1] = conversation['usage']['token'][key1]
						except: pass
						if token: result['usage']['token'][key1] = (result['usage']['token'][key1] or 0) + token
					except: pass

				tokenSystem = None
				tokenRequest = tokens.get('request')
				tokenResponse = tokens.get('response')
				if tokenRequest and context:
					# Making a request without "system": 14 Tokens - [{"role":"user","content":"list 5 good action movies"}]
					# Making a request with "system": 42 Tokens - [{"role":"system","content":"You are a chatbot that knows everything about movies and TV shows. Current date: 28 March 2023"},{"role":"user","content":"list 5 good action movies"}]
					lengthSystem = self._tokens(query[0])
					lengthRequest = self._tokens(query[1])
					tokenSystem = Math.roundDown(tokenRequest * ((lengthSystem - 1) / float(lengthSystem + lengthRequest)))
					tokenRequest -= tokenSystem

				if context: history.append(self._resultHistory(id = id, agent = Oracle.AgentSystem, refine = bool(refine), time = time1, usageToken = tokenSystem, message = context, chatbot = result))
				history.append(self._resultHistory(id = id, agent = Oracle.AgentUser, refine = bool(refine), time = time1, usageToken = tokenRequest, message = message, chatbot = result))
				history.append(self._resultHistory(id = id, agent = Oracle.AgentChatbot, refine = bool(refine), time = time2, duration = returned['duration'], usageToken = tokenResponse, message = response, chatbot = result, data = returned['data']))
				result['chat']['history'] = history
		except: Logger.error()
		return result

	##############################################################################
	# REQUEST - PLAYGROUND
	##############################################################################

	def _requestPlayground(self, message, context = None, conversation = None, refine = False, model = None, limit = None, randomness = None, creativity = None, retry = True, playground = None):
		try:
			if playground is None: playground = self.settingsPlayground()
			elif playground is True: playground = Chatgpt.PlaygroundAutomatic
			elif not playground: playground = Chatgpt.PlaygroundDisabled
			else: playground = self._playground(playground)

			if playground:
				access = self.settingsPlaygroundAccess()
				if not access: access = {}
				for i in Chatgpt.Playgrounds:
					if not i['id'] in access: access[i['id']] = 0

				playgrounds = []
				if playground == Chatgpt.PlaygroundAutomatic:
					# Use the playground that was most recently accessible.
					# Every few iterations, try a different one to distribute the load more evenly accross the playgrounds and reduce their chances of using up their limits.
					# Do not change the playground if there is a chat refinement.
					if not refine and Math.randomProbability(0.3) and len(Tools.listUnique(list(access.values()))) > 1: playgrounds = Tools.listShuffle(list(access.keys())) # Random order. Not used if all values are 0.
					else: playgrounds = sorted(access, key = access.get, reverse = True) # Ordered by largest timestamp. If all are 0, the order of Chatgpt.Playgrounds is used.
				else: playgrounds.append(playground)

				result = None
				if playgrounds:
					for i in playgrounds:
						try:
							Logger.log('Attempting to use a ChatGPT playground [%s]: %s' % (self._playgroundLabel(i), message))
							function = '_request%s' % i.lower().capitalize()
							if Tools.getFunction(instance = self, name = function): # Check if the function still exists. In case in a later version, one of the playgrounds was removed, but it is still in the user's settings.
								result = Tools.executeFunction(self, function, message = message, context = context, conversation = conversation, refine = refine, model = model, limit = limit, randomness = randomness, creativity = creativity, retry = retry)
								if result and result['success']:
									# Only do this if actual items were extracted.
									# Some playgrounds return errors messages (eg: in Chinses saying the daily credits ran out).
									# Do not label such a playground as working.
									detected = False
									self._extract(data = result) # Extract here already.
									for j in result['chat']['history']:
										if j['agent'] == Oracle.AgentChatbot and 'items' in j and j['items']:
											detected = True
											break
									if detected:
										access[i] = Time.timestamp()
										break
						except: Logger.error()

				self.settingsPlaygroundAccessSet(access)
				return result
		except: Logger.error()
		return None

	##############################################################################
	# REQUEST - ORGGPT
	##############################################################################

	def _requestOrggpt(self, message, context = None, conversation = None, refine = False, model = None, limit = None, randomness = None, creativity = None, retry = True):
		result = None
		try:
			timer = Time(start = True)
			time1 = Time.timestamp()

			result = self._result()
			result['error'] = self._requestError(type = Chatgpt.ErrorServer)

			playground = self._playground(Chatgpt.PlaygroundOrggpt, details = True)
			link = Networker.linkJoin(playground['link']['api'])

			if randomness is None: randomness = self.settingsModelRandomness(scale = False)
			if creativity is None: creativity = self.settingsModelCreativity(scale = False)

			Tools.update(result['chatbot'], {
				'playground' : playground['id'],
				'model' : playground['feature']['model'][-1] if Tools.isArray(playground['feature']['model']) else playground['feature']['model'],
				'category' : playground['feature']['category'][-1] if Tools.isArray(playground['feature']['category']) else playground['feature']['category'],
				'randomness' : randomness / 100.0,
				'creativity' : creativity / 100.0,
			})

			randomness = self._scaleRandomness(randomness)
			creativity = self._scaleCreativity(creativity)

			refine = None # No refinment possible through the API.
			history = conversation['chat']['history'] if conversation else []
			if history: id = history[-1]['id'] + (0 if refine else 1)
			else: id = 1

			data = {
				'message' : message,
				'temperature' : randomness,
				'presence_penalty' : creativity,
			}

			returned = self._request(link = link, data = data, playground = playground, retry = retry)
			time2 = Time.timestamp()

			if returned:
				try: response = returned['data']['message']
				except: response = None
				try: queryTotal = returned['data']['quota']['total']
				except: queryTotal = None
				try: queryFree = returned['data']['quota']['left']
				except: queryFree = None
				try: queryUsed = queryTotal - queryFree
				except: queryUsed = None

				Tools.update(result, {
					'success' : bool(returned['success'] and response),
					'error' : returned['error'],
					'usage' : {'query' : {'total' : queryTotal, 'free' : queryFree, 'used' : queryUsed}},
				})

				try: result['duration'] = conversation['duration']
				except: pass
				result['duration'] = (result['duration'] or 0) + max(timer.elapsed(milliseconds = True), returned['duration'] or 0) # Get the max in case a cached result was returned.

				try: result['usage']['query']['response'] = conversation['usage']['query']['response']
				except: pass
				result['usage']['query']['response'] = (result['usage']['query']['response'] or 0) + 1

				history.append(self._resultHistory(id = id, agent = Oracle.AgentUser, refine = bool(refine), time = time1, message = message, chatbot = result))
				history.append(self._resultHistory(id = id, agent = Oracle.AgentChatbot, refine = bool(refine), time = time2, duration = returned['duration'], usageQuery = 1, message = response, chatbot = result, data = returned['data']))
				result['chat']['history'] = history
		except: Logger.error()
		return result

	##############################################################################
	# REQUEST - PROXYGPT
	##############################################################################

	def _requestProxygpt(self, message, context = None, conversation = None, refine = False, model = None, limit = None, randomness = None, creativity = None, retry = True):
		result = None
		try:
			timer = Time(start = True)
			time1 = Time.timestamp()

			result = self._result()
			result['error'] = self._requestError(type = Chatgpt.ErrorServer)

			playground = self._playground(Chatgpt.PlaygroundProxygpt, details = True)
			link = Networker.linkJoin(playground['link']['api'][0])

			Tools.update(result['chatbot'], {
				'playground' : playground['id'],
				'model' : playground['feature']['model'][-1] if Tools.isArray(playground['feature']['model']) else playground['feature']['model'],
				'category' : playground['feature']['category'][-1] if Tools.isArray(playground['feature']['category']) else playground['feature']['category'],
			})

			if refine: refine = self._chatRefine(conversation)
			else: refine = None

			history = conversation['chat']['history'] if conversation else []
			if history: id = history[-1]['id'] + (0 if refine else 1)
			else: id = 1

			idParent = refine['parent_id'] if refine else None
			idSession = refine['session_id'] if refine else Tools.stringRandom(length = 16, uppercase = True, lowercase = True, digits = True, symbols = False)
			idUser = refine['user_fake_id'] if refine else Tools.stringRandom(length = 16, uppercase = True, lowercase = True, digits = True, symbols = False)

			data = {'data' : {'question' : message, 'session_id' : idSession, 'user_fake_id' : idUser}}
			if idParent: data['data']['parent_id'] = idParent

			returned = self._request(link = link, data = data, playground = playground, retry = retry)

			if returned and returned['success']:
				idChat = returned['data']['resp_data']['chat_id']

				link = Networker.linkJoin(playground['link']['api'][1])
				data = {'data' : {'chat_id' : idChat, 'session_id' : idSession, 'user_fake_id' : idUser}}

				# Website makes a request every 2 seconds.
				# Stop after 30 seconds and use whatever is available.
				for i in range(15):
					returned = self._request(link = link, data = data, playground = playground, retry = False)

					if not returned or returned['data']['resp_data']['status'] >= 3: break
					Time.sleep(2)
				time2 = Time.timestamp()
				duration = timer.elapsed(milliseconds = True)

				if returned:
					try: code = returned['data']['code_msg'].lower()
					except: code = None
					try: response = returned['data']['resp_data']['answer']
					except: response = None

					Tools.update(result, {
						'success' : bool(returned['success'] and code == 'success' and response),
						'error' : returned['error'],
						'duration' : duration,
						'chat' : {'refine' : {'parent_id' : idChat, 'session_id' : idSession, 'user_fake_id' : idUser}},
					})

					history.append(self._resultHistory(id = id, agent = Oracle.AgentUser, time = time1, message = message, chatbot = result))
					history.append(self._resultHistory(id = id, agent = Oracle.AgentChatbot, time = time2, duration = duration, message = response, chatbot = result, data = returned['data']))
					result['chat']['history'] = history
			else:
				time2 = Time.timestamp()
				duration = timer.elapsed(milliseconds = True)

				try: code = returned['data']['code_msg'].lower()
				except: code = None
				try: response = returned['data']['resp_data']['answer']
				except: response = None

				Tools.update(result, {
					'success' : bool(returned['success'] and code == 'success' and response),
					'error' : returned['error'],
				})

				try: result['duration'] = conversation['duration']
				except: pass
				result['duration'] = (result['duration'] or 0) + max(timer.elapsed(milliseconds = True), returned['duration'] or 0) # Get the max in case a cached result was returned.

				history.append(self._resultHistory(id = id, agent = Oracle.AgentUser, refine = bool(refine), time = time1, message = message, chatbot = result))
				history.append(self._resultHistory(id = id, agent = Oracle.AgentChatbot, refine = bool(refine), time = time2, duration = duration, message = response, chatbot = result, data = returned['data']))
				result['chat']['history'] = history
		except: Logger.error()
		return result

	##############################################################################
	# REQUEST - AITIANHUGPT
	##############################################################################

	def _requestAitianhugpt(self, message, context = None, conversation = None, refine = False, model = None, limit = None, randomness = None, creativity = None, retry = True):
		result = None
		try:
			timer = Time(start = True)
			time1 = Time.timestamp()

			result = self._result()
			result['error'] = self._requestError(type = Chatgpt.ErrorServer)

			playground = self._playground(Chatgpt.PlaygroundAitianhugpt, details = True)
			link = playground['link']['api'][0]

			Tools.update(result['chatbot'], {
				'playground' : playground['id'],
				'model' : playground['feature']['model'][-1] if Tools.isArray(playground['feature']['model']) else playground['feature']['model'],
				'category' : playground['feature']['category'][-1] if Tools.isArray(playground['feature']['category']) else playground['feature']['category'],
			})

			if refine: refine = self._chatRefine(conversation)
			else: refine = None

			history = conversation['chat']['history'] if conversation else []
			if history: id = history[-1]['id'] + (0 if refine else 1)
			else: id = 1

			idConversation = refine['conversationId'] if refine else None
			idParent = refine['parentMessageId'] if refine else None

			if refine: cookies = refine['cookies']
			else: cookies = self._requestCookies(link = playground['link']['web'])

			data = {'prompt' : message, 'options' : {}}
			if idConversation: data['options']['conversationId'] = idConversation
			if idParent: data['options']['parentMessageId'] = idParent

			returned = self._request(link = link, data = data, cookies = cookies, playground = playground, retry = retry, output = Chatgpt.OutputJsonStream)
			time2 = Time.timestamp()

			Tools.update(result, {
				'error' : returned['error'],
			})

			if returned and returned['success']:
				try: response = returned['data']['text']
				except: response = None
				try: idConversation = returned['data']['conversationId']
				except: idConversation = None
				try: idParent = returned['data']['id']
				except: idParent = None
				Tools.update(result, {
					'success' : bool(returned['success'] and response),
					'chat' : {'refine' : {'conversationId' : idConversation, 'parentMessageId' : idParent, 'cookies' : cookies}},
				})
			else:
				try: response = returned['data']['message']
				except: response = None
				Tools.update(result, {
					'success' : False,
				})

			try: result['duration'] = conversation['duration']
			except: pass
			result['duration'] = (result['duration'] or 0) + max(timer.elapsed(milliseconds = True), returned['duration'] or 0) # Get the max in case a cached result was returned.

			history.append(self._resultHistory(id = id, agent = Oracle.AgentUser, refine = bool(refine), time = time1, message = message, chatbot = result))
			history.append(self._resultHistory(id = id, agent = Oracle.AgentChatbot, refine = bool(refine), time = time2, duration = returned['duration'], message = response, chatbot = result, data = returned['data']))
			result['chat']['history'] = history
		except: Logger.error()
		return result

	##############################################################################
	# REQUEST - YQCLOUDGPT
	##############################################################################

	def _requestYqcloudgpt(self, message, context = None, conversation = None, refine = False, model = None, limit = None, randomness = None, creativity = None, retry = True):
		result = None
		try:
			timer = Time(start = True)
			time1 = Time.timestamp()

			result = self._result()
			result['error'] = self._requestError(type = Chatgpt.ErrorServer)

			playground = self._playground(Chatgpt.PlaygroundYqcloudgpt, details = True)
			link = playground['link']['api'][0]

			Tools.update(result['chatbot'], {
				'playground' : playground['id'],
				'model' : playground['feature']['model'][-1] if Tools.isArray(playground['feature']['model']) else playground['feature']['model'],
				'category' : playground['feature']['category'][-1] if Tools.isArray(playground['feature']['category']) else playground['feature']['category'],
			})

			if refine: refine = self._chatRefine(conversation)
			else: refine = None

			history = conversation['chat']['history'] if conversation else []
			if history: id = history[-1]['id'] + (0 if refine else 1)
			else: id = 1

			if refine: idUser = refine['userId']
			else: idUser = Time.timestamp(milliseconds = True)

			data = {'prompt' : message, 'userId' : '#/chat/%d' % idUser, 'network' : True, 'system' : context[0] if context else None, 'withoutContext' : False, 'stream' : False}
			returned = self._request(link = link, data = data, playground = playground, retry = retry, output = Chatgpt.OutputText)
			time2 = Time.timestamp()

			Tools.update(result, {
				'error' : returned['error'],
			})

			if returned and returned['success']:
				try: response = returned['data']
				except: response = None
				Tools.update(result, {
					'success' : bool(returned['success'] and response),
					'chat' : {'refine' : {'userId' : idUser}},
				})
			else:
				try: response = returned['data']
				except: response = None
				Tools.update(result, {
					'success' : False,
				})

			try: result['duration'] = conversation['duration']
			except: pass
			result['duration'] = (result['duration'] or 0) + max(timer.elapsed(milliseconds = True), returned['duration'] or 0) # Get the max in case a cached result was returned.

			history.append(self._resultHistory(id = id, agent = Oracle.AgentUser, refine = bool(refine), time = time1, message = message, chatbot = result))
			history.append(self._resultHistory(id = id, agent = Oracle.AgentChatbot, refine = bool(refine), time = time2, duration = returned['duration'], message = response, chatbot = result, data = returned['data']))
			result['chat']['history'] = history
		except: Logger.error()
		return result

	##############################################################################
	# REQUEST - AIANSWERGPT
	##############################################################################

	def _requestAianswergpt(self, message, context = None, conversation = None, refine = False, model = None, limit = None, randomness = None, creativity = None, retry = True):
		result = None
		try:
			timer = Time(start = True)
			time1 = Time.timestamp()

			result = self._result()
			result['error'] = self._requestError(type = Chatgpt.ErrorServer)

			playground = self._playground(Chatgpt.PlaygroundAianswergpt, details = True)
			link = playground['link']['api'][0]

			Tools.update(result['chatbot'], {
				'playground' : playground['id'],
				'model' : playground['feature']['model'][-1] if Tools.isArray(playground['feature']['model']) else playground['feature']['model'],
				'category' : playground['feature']['category'][-1] if Tools.isArray(playground['feature']['category']) else playground['feature']['category'],
			})

			if refine: refine = self._chatRefine(conversation)
			else: refine = None

			history = conversation['chat']['history'] if conversation else []
			if history: id = history[-1]['id'] + (0 if refine else 1)
			else: id = 1

			data = {'msg' : message, 'token' : '', 'style' : '0'} # style = '0' seems to be ChatGPT3.5. style = '2' seems to be ChatGPT4 (does not work atm).
			returned = self._request(link = link, data = data, playground = playground, retry = retry)
			time2 = Time.timestamp()

			Tools.update(result, {
				'error' : returned['error'],
			})

			if returned and returned['success']:
				try: response = ' '.join(returned['data']['data']) if Tools.isArray(returned['data']['data']) else returned['data']['data']
				except: response = None
				Tools.update(result, {
					'success' : bool(returned['success'] and response),
				})
			else:
				try: response = ' '.join(returned['data']['data']) if Tools.isArray(returned['data']['data']) else returned['data']['data']
				except: response = None
				Tools.update(result, {
					'success' : False,
				})

			if response: response = response.replace('\uff08\u5982\u672a\u663e\u793a\u5b8c\u5168\uff0c\u8bf7\u586b\u5199APIKEY\u83b7\u53d6\u5b8c\u6574\u6d88\u606f\uff09', '')

			try: result['duration'] = conversation['duration']
			except: pass
			result['duration'] = (result['duration'] or 0) + max(timer.elapsed(milliseconds = True), returned['duration'] or 0) # Get the max in case a cached result was returned.

			history.append(self._resultHistory(id = id, agent = Oracle.AgentUser, refine = bool(refine), time = time1, message = message, chatbot = result))
			history.append(self._resultHistory(id = id, agent = Oracle.AgentChatbot, refine = bool(refine), time = time2, duration = returned['duration'], message = response, chatbot = result, data = returned['data']))
			result['chat']['history'] = history
		except: Logger.error()
		return result

	##############################################################################
	# REQUEST - FASTGPT
	##############################################################################

	def _requestFastgpt(self, message, context = None, conversation = None, refine = False, model = None, limit = None, randomness = None, creativity = None, retry = True):
		result = None
		try:
			timer = Time(start = True)
			time1 = Time.timestamp()

			result = self._result()
			result['error'] = self._requestError(type = Chatgpt.ErrorServer)

			playground = self._playground(Chatgpt.PlaygroundFastgpt, details = True)
			link = playground['link']['api'][0]

			model = self._model(model = model, details = True, default = True)
			category = self._category(category = model['category'], details = True)

			if refine and category['refine']: refine = self._chatRefine(conversation)
			else: refine = None

			if refine: cookies = refine['cookies']
			else: cookies = self._requestCookies(link = playground['link']['web'])

			idMessage = Hash.uuid()
			if refine: idParent = refine['parent_message_id']
			else: idParent = None

			history = conversation['chat']['history'] if conversation else []
			if history: id = history[-1]['id'] + (0 if refine else 1)
			else: id = 1

			Tools.update(result['chatbot'], {
				'playground' : playground['id'],
				'model' : model['id'] if model else playground['feature']['model'][-1] if Tools.isArray(playground['feature']['model']) else playground['feature']['model'],
				'category' : category['id'] if category else playground['feature']['category'][-1] if Tools.isArray(playground['feature']['category']) else playground['feature']['category'],
			})

			query = [{'role' : 'user', 'content' : message}]

			# This is seen as the prompt, instead of the actual message.
			#if context and (not history or not refine): query.insert(0, {'role' : 'system', 'content' : context[0] if Tools.isArray(context) else context})

			for i in query:
				if i['role'] == 'user': i['id'] = idMessage
				i['author'] = {'role': i['role']}
				i['content'] = {'content_type': 'text', 'parts' : [i['content']]}

			data = {
				'action' : 'next',
				'model' : model['id'],
				'stream' : False,
				'messages' : query,
			}
			if idParent: data['parent_message_id'] = idParent

			returned = self._request(link = link, data = data, cookies = cookies, playground = playground, retry = retry, output = ['.*data\s*:\s*(\{.*?\})\n', Chatgpt.OutputJson])
			time2 = Time.timestamp()

			Tools.update(result, {
				'error' : returned['error'],
			})

			if returned and returned['success']:
				try: response = ' '.join(returned['data']['message']['content']['parts'])
				except: response = None
				try: parent = returned['data']['message']['id']
				except: parent = None
				Tools.update(result, {
					'success' : bool(returned['success'] and response),
					'chat' : {'refine' : {'parent_message_id' : parent, 'cookies' : cookies}},
				})
			else:
				try: response = Converter.jsonTo(returned['data']['message'])
				except: response = None
				Tools.update(result, {
					'success' : False,
				})

			try: result['duration'] = conversation['duration']
			except: pass
			result['duration'] = (result['duration'] or 0) + max(timer.elapsed(milliseconds = True), returned['duration'] or 0) # Get the max in case a cached result was returned.

			#if context: history.append(self._resultHistory(id = id, agent = Oracle.AgentSystem, refine = bool(refine), time = time1, message = context, chatbot = result))
			history.append(self._resultHistory(id = id, agent = Oracle.AgentUser, refine = bool(refine), time = time1, message = message, chatbot = result))
			history.append(self._resultHistory(id = id, agent = Oracle.AgentChatbot, refine = bool(refine), time = time2, duration = returned['duration'], message = response, chatbot = result, data = returned['data']))
			result['chat']['history'] = history
		except: Logger.error()
		return result

	##############################################################################
	# REQUEST - UNLIGPT
	##############################################################################

	def _requestUnligpt(self, message, context = None, conversation = None, refine = False, model = None, limit = None, randomness = None, creativity = None, retry = True):
		result = None
		try:
			timer = Time(start = True)
			time1 = Time.timestamp()

			result = self._result()
			result['error'] = self._requestError(type = Chatgpt.ErrorServer)

			playground = self._playground(Chatgpt.PlaygroundUnligpt, details = True)
			link = playground['link']['api'][0]

			model = self._model(model = model, details = True, default = True)
			category = self._category(category = model['category'], details = True)

			if refine and category['refine']: refine = self._chatRefine(conversation)
			else: refine = None

			if refine: idBot = refine['botId']
			else: idBot = 'default'
			if refine: idSession = refine['session']
			else: idSession = 'N/A'
			if refine: idClient = refine['clientId']
			else: idClient = Tools.stringRandom(length = 11, uppercase = False, lowercase = True, digits = True, symbols = False)
			if refine: idContext = refine['contextId']
			else: idContext = Math.random(start = 100, end = 999)
			idMessage = Tools.stringRandom(length = 11, uppercase = False, lowercase = True, digits = True, symbols = False)
			idResponse = Tools.stringRandom(length = 11, uppercase = False, lowercase = True, digits = True, symbols = False)

			messages = []
			if refine: messages = refine['messages']

			history = conversation['chat']['history'] if conversation else []
			if history: id = history[-1]['id'] + (0 if refine else 1)
			else: id = 1

			Tools.update(result['chatbot'], {
				'playground' : playground['id'],
				'model' : model['id'] if model else playground['feature']['model'][-1] if Tools.isArray(playground['feature']['model']) else playground['feature']['model'],
				'category' : category['id'] if category else playground['feature']['category'][-1] if Tools.isArray(playground['feature']['category']) else playground['feature']['category'],
			})

			data = {
				'id' : 'default',
				'botId' : idBot,
				'session' : idSession,
				'clientId' : idClient,
				'contextId' : idContext,
				'newMessage' : message,
				'messages' : Tools.copy(messages), # Edited afterwards.
			}

			messages.append({
				'id' : idMessage,
				'role' : 'user',
				'content' : message,
				'timestamp' : Time.timestamp(milliseconds = True)
			})

			returned = self._request(link = link, data = data, playground = playground, retry = retry)
			time2 = Time.timestamp()

			try: response = returned['data']['reply']
			except: response = None
			try: success = bool(returned['success'] and returned['data']['success'] and response)
			except: success = False

			if success:
				messages.append({
					'id' : idResponse,
					'role' : 'assistant',
					'content' : response,
					'timestamp' : Time.timestamp(milliseconds = True)
				})

			Tools.update(result, {
				'success' : success,
				'error' : returned['error'],
				'chat' : {'refine' : {'session' : idSession, 'botId' : idBot, 'clientId' : idClient, 'contextId' : idContext, 'messages' : messages}},
			})

			try: result['duration'] = conversation['duration']
			except: pass
			result['duration'] = (result['duration'] or 0) + max(timer.elapsed(milliseconds = True), returned['duration'] or 0) # Get the max in case a cached result was returned.

			history.append(self._resultHistory(id = id, agent = Oracle.AgentUser, refine = bool(refine), time = time1, message = message, chatbot = result))
			history.append(self._resultHistory(id = id, agent = Oracle.AgentChatbot, refine = bool(refine), time = time2, duration = returned['duration'], message = response, chatbot = result, data = returned['data']))
			result['chat']['history'] = history
		except: Logger.error()
		return result

	##############################################################################
	# REQUEST - AIASKGPT
	##############################################################################

	def _requestAiaskgpt(self, message, context = None, conversation = None, refine = False, model = None, limit = None, randomness = None, creativity = None, retry = True):
		result = None
		try:
			timer = Time(start = True)
			time1 = Time.timestamp()

			result = self._result()
			result['error'] = self._requestError(type = Chatgpt.ErrorServer)

			playground = self._playground(Chatgpt.PlaygroundAiaskgpt, details = True)
			link = playground['link']['api'][0]

			model = self._model(model = model, details = True, default = True)
			category = self._category(category = model['category'], details = True)

			if refine and category['refine']: refine = self._chatRefine(conversation)
			else: refine = None

			if refine: idChat = refine['id']
			else: idChat = Tools.stringRandom(length = 21, uppercase = True, lowercase = True, digits = False, symbols = False)

			history = conversation['chat']['history'] if conversation else []
			if history: id = history[-1]['id'] + (0 if refine else 1)
			else: id = 1

			if randomness is None: randomness = self.settingsModelRandomness(scale = False)
			Tools.update(result['chatbot'], {
				'playground' : playground['id'],
				'model' : model['id'] if model else playground['feature']['model'][-1] if Tools.isArray(playground['feature']['model']) else playground['feature']['model'],
				'category' : category['id'] if category else playground['feature']['category'][-1] if Tools.isArray(playground['feature']['category']) else playground['feature']['category'],
				'randomness' : randomness / 100.0,
			})
			randomness = self._scaleRandomness(randomness)

			messages = []
			if refine: messages = refine['list']

			if not refine and context:
				# Remove the date from the context message, otherwise the chatbot complaints with:
				#	As an AI language model, I do not have a conception of time. So, I cannot provide any information on movies that were released or events that happened after my last update.
				# Since this does not happen with other playgrounds or the official API, I think that this playground sends the context as a normal 1st prompt, instead of as a system message.
				# Update: remove the context completely, since it confuses the chatbot too much. Even without the date, we get replies like:
				#	That's correct! I am an AI-powered chatbot programmed to provide information and insights about everything related to movies. From classic films to the latest blockbusters, I've got it covered! Whether you're looking for movie recommendations, trivia, or analysis, I'm here to help. Let me know if you have any questions or requests!
				# which further indicates that the context is sent as a normal message.
				# Update: It seems that the context is required, otherwise the chatbot just returns random answers.
				context = context[0] if Tools.isArray(context) else context
				#context = Regex.remove(data = context, expression = r'\.([a-z\s]+\:?\s*\d{1,2}\s*[a-z]+\s*\d{4}\s*(?:$|[\.\,\!]))', group = 1)
				#context = Regex.remove(data = context, expression = r'\.(\s*\d{1,2}\s*[a-z]+\s*\d{4}\s*(?:$|[\.\,\!]))', group = 1)
				messages.append({
					'role' : 'assistant',
					'isMe' : False,
					'nickname' : '',
					'content' : context,
					'time' : Time.format(format = Time.FormatTime),
				})

			# NB: The list is reversed. The context comes last and the prompts first.
			# Any other way results in the chatbot returning random responses.
			messages.insert(0, {
				'role' : 'user',
				'isMe' : True,
				'nickname' : '',
				'content' : message,
				'time' : Time.format(format = Time.FormatTime),
			})

			data = {
				'id' : idChat,
				'temperature' : randomness,
				'models' : '0', # 0 = ChatGPT3.5 (free), 1 = ChatGPT4.0 (requires login).
				'continuous' : True,
				'title' : message,
				'prompt' : '', # Yes, for some reason the message is posted as the title, not the prompt.
				'list' : messages,
			}

			returned = self._request(link = link, data = data, playground = playground, retry = retry, output = Chatgpt.OutputText)
			time2 = Time.timestamp()

			try: response = returned['data']
			except: response = None
			try: success = bool(returned['success'] and response)
			except: success = False

			if success:
				messages.insert(0, {
					'role' : 'assistant',
					'isMe' : False,
					'content' : response,
					'time' : Time.format(format = Time.FormatTime),
				})

			Tools.update(result, {
				'success' : success,
				'error' : returned['error'],
				'chat' : {'refine' : {'id' : idChat, 'list' : messages}},
			})

			try: result['duration'] = conversation['duration']
			except: pass
			result['duration'] = (result['duration'] or 0) + max(timer.elapsed(milliseconds = True), returned['duration'] or 0) # Get the max in case a cached result was returned.

			if context and not refine: history.append(self._resultHistory(id = id, agent = Oracle.AgentSystem, refine = bool(refine), time = time1, message = context, chatbot = result))
			history.append(self._resultHistory(id = id, agent = Oracle.AgentUser, refine = bool(refine), time = time1, message = message, chatbot = result))
			history.append(self._resultHistory(id = id, agent = Oracle.AgentChatbot, refine = bool(refine), time = time2, duration = returned['duration'], message = response, chatbot = result, data = returned['data']))
			result['chat']['history'] = history
		except: Logger.error()
		return result
