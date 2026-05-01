#!/usr/bin/env ruby
# frozen_string_literal: true

require 'xcodeproj'

PROJECT_PATH = File.expand_path('../frontend/ios/App/App.xcodeproj', __dir__)
WATCH_SOURCE_DIR = '../WatchCompanion'
WATCH_SUPPORT_DIR = '../WatchCompanionApp'
WATCH_TARGET_NAME = 'CacaRadarWatch'
WATCH_EXTENSION_TARGET_NAME = 'CacaRadarWatchExtension'
WATCH_BUNDLE_ID = 'com.jefe.cacaradar.watchkitapp'
WATCH_EXTENSION_BUNDLE_ID = 'com.jefe.cacaradar.watchkitapp.watchkitextension'
WATCH_DEPLOYMENT_TARGET = '10.0'

project = Xcodeproj::Project.open(PROJECT_PATH)
app_target = project.targets.find { |target| target.name == 'App' }
raise 'App target not found' unless app_target

project.root_object.attributes['LastUpgradeCheck'] = '1600'
project.root_object.attributes['LastSwiftUpdateCheck'] = '1600'

watch_group =
  project.main_group.children.find { |child| child.isa == 'PBXGroup' && child.display_name == 'WatchCompanion' } ||
  project.main_group.new_group('WatchCompanion', WATCH_SOURCE_DIR)
watch_group.set_source_tree('<group>')

support_group =
  project.main_group.children.find { |child| child.isa == 'PBXGroup' && child.display_name == 'WatchCompanionApp' } ||
  project.main_group.new_group('WatchCompanionApp', WATCH_SUPPORT_DIR)
support_group.set_source_tree('<group>')

source_refs = %w[
  CacaRadarWatchApp.swift
  ContentView.swift
  PhoneSessionBridge.swift
].map do |filename|
  watch_group.files.find { |child| child.path == filename } || watch_group.new_file(filename)
end

support_group.files.find { |child| child.path == 'Info.plist' } || support_group.new_file('Info.plist')
support_group.files.find { |child| child.path == 'Extension-Info.plist' } || support_group.new_file('Extension-Info.plist')

watch_target = project.targets.find { |target| target.name == WATCH_TARGET_NAME }
unless watch_target
  watch_target = project.new_target(:watch2_app, WATCH_TARGET_NAME, :watchos, WATCH_DEPLOYMENT_TARGET, project.products_group, :swift, WATCH_TARGET_NAME)
end

watch_extension_target = project.targets.find { |target| target.name == WATCH_EXTENSION_TARGET_NAME }
unless watch_extension_target
  watch_extension_target = project.new_target(:watch2_extension, WATCH_EXTENSION_TARGET_NAME, :watchos, WATCH_DEPLOYMENT_TARGET, project.products_group, :swift, WATCH_EXTENSION_TARGET_NAME)
end

watch_target.source_build_phase.files.to_a.each(&:remove_from_project)

existing_extension_paths = watch_extension_target.source_build_phase.files_references.map(&:path)
source_refs.each do |file_ref|
  watch_extension_target.source_build_phase.add_file_reference(file_ref, true) unless existing_extension_paths.include?(file_ref.path)
end

watch_target.build_configurations.each do |config|
  build_settings = config.build_settings
  build_settings['CODE_SIGN_STYLE'] = 'Automatic'
  build_settings['CURRENT_PROJECT_VERSION'] = '25'
  build_settings['DEVELOPMENT_TEAM'] = 'Z3SH6Z4GL6'
  build_settings['GENERATE_INFOPLIST_FILE'] = 'NO'
  build_settings['INFOPLIST_FILE'] = '../WatchCompanionApp/Info.plist'
  build_settings['MARKETING_VERSION'] = '1.1.23'
  build_settings['PRODUCT_BUNDLE_IDENTIFIER'] = WATCH_BUNDLE_ID
  build_settings['PRODUCT_NAME'] = WATCH_TARGET_NAME
  build_settings['SDKROOT'] = 'watchos'
  build_settings['SKIP_INSTALL'] = 'YES'
  build_settings['SUPPORTED_PLATFORMS'] = 'watchos watchsimulator'
  build_settings['SWIFT_VERSION'] = '5.0'
  build_settings['TARGETED_DEVICE_FAMILY'] = '4'
  build_settings['WATCHOS_DEPLOYMENT_TARGET'] = WATCH_DEPLOYMENT_TARGET
end

watch_extension_target.build_configurations.each do |config|
  build_settings = config.build_settings
  build_settings['APPLICATION_EXTENSION_API_ONLY'] = 'YES'
  build_settings['CODE_SIGN_STYLE'] = 'Automatic'
  build_settings['CURRENT_PROJECT_VERSION'] = '25'
  build_settings['DEVELOPMENT_TEAM'] = 'Z3SH6Z4GL6'
  build_settings['GENERATE_INFOPLIST_FILE'] = 'NO'
  build_settings['INFOPLIST_FILE'] = '../WatchCompanionApp/Extension-Info.plist'
  build_settings['LD_RUNPATH_SEARCH_PATHS'] = ['$(inherited)', '@executable_path/Frameworks']
  build_settings['MARKETING_VERSION'] = '1.1.23'
  build_settings['PRODUCT_BUNDLE_IDENTIFIER'] = WATCH_EXTENSION_BUNDLE_ID
  build_settings['PRODUCT_NAME'] = WATCH_EXTENSION_TARGET_NAME
  build_settings['SDKROOT'] = 'watchos'
  build_settings['SKIP_INSTALL'] = 'YES'
  build_settings['SUPPORTED_PLATFORMS'] = 'watchos watchsimulator'
  build_settings['SWIFT_VERSION'] = '5.0'
  build_settings['TARGETED_DEVICE_FAMILY'] = '4'
  build_settings['WATCHOS_DEPLOYMENT_TARGET'] = WATCH_DEPLOYMENT_TARGET
end

watch_target.frameworks_build_phase.files.to_a.each(&:remove_from_project)
watch_extension_target.frameworks_build_phase.files.to_a.each(&:remove_from_project)

frameworks_group = project.main_group.children.find { |child| child.isa == 'PBXGroup' && child.display_name == 'Frameworks' }
watchos_group = frameworks_group&.children&.find { |child| child.isa == 'PBXGroup' && child.display_name == 'watchOS' }
watchos_group&.children&.each(&:remove_from_project)
watchos_group&.remove_from_project if watchos_group && watchos_group.children.empty?
frameworks_group&.remove_from_project if frameworks_group && frameworks_group.children.empty?

target_attributes = project.root_object.attributes['TargetAttributes'] ||= {}
target_attributes[watch_target.uuid] ||= {}
target_attributes[watch_target.uuid]['CreatedOnToolsVersion'] ||= '16.0'
target_attributes[watch_target.uuid]['DevelopmentTeam'] = 'Z3SH6Z4GL6'
target_attributes[watch_target.uuid]['ProvisioningStyle'] = 'Automatic'

target_attributes[watch_extension_target.uuid] ||= {}
target_attributes[watch_extension_target.uuid]['CreatedOnToolsVersion'] ||= '16.0'
target_attributes[watch_extension_target.uuid]['DevelopmentTeam'] = 'Z3SH6Z4GL6'
target_attributes[watch_extension_target.uuid]['ProvisioningStyle'] = 'Automatic'

unless watch_target.dependencies.any? { |dependency| dependency.target == watch_extension_target }
  watch_target.add_dependency(watch_extension_target)
end

watch_embed_phase =
  watch_target.copy_files_build_phases.find { |phase| phase.name == 'Embed App Extensions' } ||
  watch_target.new_copy_files_build_phase('Embed App Extensions')
watch_embed_phase.dst_subfolder_spec = '13'
watch_embed_phase.run_only_for_deployment_postprocessing = '0'
unless watch_embed_phase.files_references.any? { |file_ref| file_ref.uuid == watch_extension_target.product_reference.uuid }
  watch_embed_phase.add_file_reference(watch_extension_target.product_reference, true)
end

unless app_target.dependencies.any? { |dependency| dependency.target == watch_target }
  app_target.add_dependency(watch_target)
end

embed_phase =
  app_target.copy_files_build_phases.find { |phase| phase.name == 'Embed Watch Content' } ||
  app_target.new_copy_files_build_phase('Embed Watch Content')
embed_phase.dst_subfolder_spec = '16'
embed_phase.run_only_for_deployment_postprocessing = '0'

unless embed_phase.files_references.any? { |file_ref| file_ref.uuid == watch_target.product_reference.uuid }
  embed_phase.add_file_reference(watch_target.product_reference, true)
end

project.save
