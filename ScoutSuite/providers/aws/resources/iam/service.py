import asyncio

from ScoutSuite.providers.aws.resources.resources import AWSCompositeResources
from ScoutSuite.providers.aws.resources.iam.credentialreports import CredentialReports
from ScoutSuite.providers.aws.resources.iam.groups import Groups
from ScoutSuite.providers.aws.resources.iam.policies import Policies
from ScoutSuite.providers.aws.resources.iam.users import Users
from ScoutSuite.providers.aws.resources.iam.roles import Roles
from ScoutSuite.providers.aws.facade.facade import AWSFacade


class IAM(AWSCompositeResources):
    _children = [
        (CredentialReports, 'credential_reports'),
        (Groups, 'groups'),
        (Policies, 'policies'),
        (Users, 'users'),
        (Roles, 'roles')
    ]

    def __init__(self):
        # TODO: Should be injected
        self.facade = AWSFacade()
        self.service = 'iam'

    async def fetch_all(self, credentials, regions=None, partition_name='aws'):
        # TODO: This should not be set here, the facade should be injected and already authenticated
        self.facade._set_session(credentials)
        await self._fetch_children(self, {})

    def finalize(self):
        # Update permissions for managed policies
        for policy in self['policies'].values():
            policy_id = policy['id']
            if 'attached_to' in policy and len(policy['attached_to']) > 0:
                for entity_type in policy['attached_to']:
                    for entity in policy['attached_to'][entity_type]:
                        entity['id'] = self._get_id_for_resource(entity_type, entity['name'])
                        entities = self[entity_type] 
                        entities[entity['id']]['policies'] = [] # TODO : if does not exist
                        entities[entity['id']]['policies_counts'] = 0 # TODO : if does not exist
                        entities[entity['id']]['policies'].append(policy_id)
                        entities[entity['id']]['policies_counts'] += 1
                # self._parse_permissions(policy_id, policy['PolicyDocument'], 'policies', entity_type, entity['id'])
            else:
                pass
                # self._parse_permissions(policy_id, policy['PolicyDocument'], 'policies', None, None)

    def _get_id_for_resource(self, iam_resource_type, resource_name):
        for resource_id in self[iam_resource_type]:
            if self[iam_resource_type][resource_id]['name'] == resource_name:
                return resource_id

    def _parse_permissions(self, policy_name, policy_document, policy_type, iam_resource_type, resource_name):
        # Enforce list of statements (Github issue #99)
        if type(policy_document['Statement']) != list:
            policy_document['Statement'] = [policy_document['Statement']]
        for statement in policy_document['Statement']:
            self._parse_statement(policy_name, statement, policy_type, iam_resource_type, resource_name)

    def _parse_statement(self, policy_name, statement, policy_type, iam_resource_type, resource_name):
        # Effect
        effect = str(statement['Effect'])
        # Action or NotAction
        action_string = 'Action' if 'Action' in statement else 'NotAction'
        if type(statement[action_string]) != list:
            statement[action_string] = [statement[action_string]]
        # Resource or NotResource
        resource_string = 'Resource' if 'Resource' in statement else 'NotResource'
        if type(statement[resource_string]) != list:
            statement[resource_string] = [statement[resource_string]]
        # Condition
        condition = statement['Condition'] if 'Condition' in statement else None
        self['permissions'][action_string] = {} # TODO: If does not exist
        if iam_resource_type is None:
            return
        self._parse_actions(effect, action_string, statement[action_string], resource_string,
                             statement[resource_string], iam_resource_type, resource_name, policy_name, policy_type,
                             condition)

    def _parse_actions(self, effect, action_string, actions, resource_string, resources, iam_resource_type,
                        iam_resource_name, policy_name, policy_type, condition):
        for action in actions:
            self['permissions'][action_string][action] = {} # TODO: If does not exist
            self['permissions'][action_string][action][iam_resource_type] = {} # TODO: If does not exist
            self['permissions'][action_string][action][iam_resource_type][effect] = {} # TODO: If does not exist
            self['permissions'][action_string][action][iam_resource_type][effect][iam_resource_name] = {} # TODO: If does not exist
            self._parse_action(effect, action_string, action, resource_string, resources, iam_resource_type,
                                iam_resource_name, policy_name, policy_type, condition)

    def _parse_action(self, effect, action_string, action, resource_string, resources, iam_resource_type,
                       iam_resource_name, policy_name, policy_type, condition):
        for resource in resources:
            self._parse_resource(effect, action_string, action, resource_string, resource, iam_resource_type,
                                  iam_resource_name, policy_name, policy_type, condition)

    def _parse_resource(self, effect, action_string, action, resource_string, resource, iam_resource_type, iam_resource_name, policy_name, policy_type, condition):
        self['permissions'][action_string][action][iam_resource_type][effect][iam_resource_name][resource_string] = {} # TODO: If does not exist
        self['permissions'][action_string][action][iam_resource_type][effect][iam_resource_name][resource_string][resource] = {} # TODO: If does not exist
        self['permissions'][action_string][action][iam_resource_type][effect][iam_resource_name][resource_string][resource][policy_type] = {} # TODO: If does not exist
        self['permissions'][action_string][action][iam_resource_type][effect][iam_resource_name][resource_string][resource][policy_type][policy_name] = {} # TODO: If does not exist
        self['permissions'][action_string][action][iam_resource_type][effect][iam_resource_name][resource_string][resource][policy_type][policy_name]['condition'] = condition
