
(cl:in-package :asdf)

(defsystem "game_msgs-msg"
  :depends-on (:roslisp-msg-protocol :roslisp-utils )
  :components ((:file "_package")
    (:file "GameUserMsg" :depends-on ("_package_GameUserMsg"))
    (:file "_package_GameUserMsg" :depends-on ("_package"))
  ))