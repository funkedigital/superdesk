define(['angular', 'lodash'], function(angular, _) {
    'use strict';

    return angular.module('superdesk.services.preferencesService', [])

        .service('preferencesService', ['$injector', '$rootScope', '$q', 'storage',
            function($injector, $rootScope, $q, storage) {

            var USER_PREFERENCES = 'user_preferences',
                SESSION_PREFERENCES = 'session_preferences',
                PREFERENCES = 'preferences',
                userPreferences = ['feature:preview', 'archive:view', 'email:notification', 'workqueue:items'],
                //sessionPreferences = ['scratchpad:items', 'pinned:items', 'desk:items'],
                api,
                defer,
                original_preferences = null;

            function saveLocally(preferences, type, key) {

                //console.log('saving saveLocally:', preferences, type, key);

                if (type && key && original_preferences)
                {
                    original_preferences[type][key] = preferences[type][key];
                    original_preferences._etag = preferences._etag;
                } else
                {
                    original_preferences = preferences;
                }

                //console.log('saved saveLocally:', this.original_preferences);

                storage.setItem(PREFERENCES, original_preferences);
            }

            function loadLocally()
            {
                if (!original_preferences)
                {
                    original_preferences = storage.getItem(PREFERENCES);
                }

                return original_preferences;
            }

            this.remove = function() {
                storage.removeItem(PREFERENCES);
                original_preferences = null;
            };

            function getPreferences(sessionId) {
                if (!api) { api = $injector.get('api'); }

                defer = $q.defer();
                api('preferences').getById(sessionId)
                    .then(function(result) {
                        return defer.resolve(result);
                    });

                return defer.promise;
            }

            this.get = function(key) {

                var original_prefs = loadLocally();

                if (!original_prefs){

                    if ($rootScope.sessionId){
                        getPreferences($rootScope.sessionId).then(function(preferences) {

                            saveLocally(preferences);
                            original_prefs = preferences;

                            if (!key){
                                return original_prefs[USER_PREFERENCES];
                            } else if (userPreferences.indexOf(key) >= 0) {
                                return original_prefs[USER_PREFERENCES][key];
                            } else {
                                return original_prefs[SESSION_PREFERENCES][key];
                            }

                        });
                    } else {
                        return null;
                    }
                } else {
                    if (!key){
                        return original_prefs[USER_PREFERENCES];
                    } else if (userPreferences.indexOf(key) >= 0) {
                        var prefs = original_prefs[USER_PREFERENCES] || {};
                        return prefs[key] || null;
                    } else {
                        var sess_prefs = original_prefs[SESSION_PREFERENCES] || {};
                        return sess_prefs[key] || null;
                    }
                }
            };

            this.update = function(updates, key) {
                if (!key){
                    return updatePreferences(updates);
                } else if (userPreferences.indexOf(key) >= 0) {
                    return updatePreferences(USER_PREFERENCES, updates, key);
                } else {
                    return updatePreferences(SESSION_PREFERENCES, updates, key);
                }
            };

            function updatePreferences (type, updates, key) {

                var original_prefs = _.cloneDeep(loadLocally());
                var user_updates = {};
                user_updates[type] = updates;

                if (!api) { api = $injector.get('api'); }

                defer = $q.defer();

                api('preferences', $rootScope.sessionId).save(original_prefs, user_updates)
                    .then(function(result) {
                                saveLocally(result, type, key);
                                return defer.resolve(result);
                            },
                            function(response) {
                                console.log('patch err response:', response);
                                return defer.reject(response);
                        });

                return defer.promise;

            }

    }]);

});
