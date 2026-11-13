; Auto-generated. Do not edit!


(cl:in-package game_msgs-msg)


;//! \htmlinclude GameUserMsg.msg.html

(cl:defclass <GameUserMsg> (roslisp-msg-protocol:ros-message)
  ((name
    :reader name
    :initarg :name
    :type cl:string
    :initform "")
   (username
    :reader username
    :initarg :username
    :type cl:string
    :initform "")
   (age
    :reader age
    :initarg :age
    :type cl:integer
    :initform 0))
)

(cl:defclass GameUserMsg (<GameUserMsg>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <GameUserMsg>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'GameUserMsg)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name game_msgs-msg:<GameUserMsg> is deprecated: use game_msgs-msg:GameUserMsg instead.")))

(cl:ensure-generic-function 'name-val :lambda-list '(m))
(cl:defmethod name-val ((m <GameUserMsg>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader game_msgs-msg:name-val is deprecated.  Use game_msgs-msg:name instead.")
  (name m))

(cl:ensure-generic-function 'username-val :lambda-list '(m))
(cl:defmethod username-val ((m <GameUserMsg>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader game_msgs-msg:username-val is deprecated.  Use game_msgs-msg:username instead.")
  (username m))

(cl:ensure-generic-function 'age-val :lambda-list '(m))
(cl:defmethod age-val ((m <GameUserMsg>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader game_msgs-msg:age-val is deprecated.  Use game_msgs-msg:age instead.")
  (age m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <GameUserMsg>) ostream)
  "Serializes a message object of type '<GameUserMsg>"
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'name))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'name))
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'username))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'username))
  (cl:let* ((signed (cl:slot-value msg 'age)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 18446744073709551616) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 32) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 40) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 48) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 56) unsigned) ostream)
    )
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <GameUserMsg>) istream)
  "Deserializes a message object of type '<GameUserMsg>"
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'name) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'name) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'username) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'username) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 32) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 40) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 48) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 56) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'age) (cl:if (cl:< unsigned 9223372036854775808) unsigned (cl:- unsigned 18446744073709551616))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<GameUserMsg>)))
  "Returns string type for a message object of type '<GameUserMsg>"
  "game_msgs/GameUserMsg")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'GameUserMsg)))
  "Returns string type for a message object of type 'GameUserMsg"
  "game_msgs/GameUserMsg")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<GameUserMsg>)))
  "Returns md5sum for a message object of type '<GameUserMsg>"
  "76ad7cc8793d3811f3fd0e458252b5c3")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'GameUserMsg)))
  "Returns md5sum for a message object of type 'GameUserMsg"
  "76ad7cc8793d3811f3fd0e458252b5c3")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<GameUserMsg>)))
  "Returns full string definition for message of type '<GameUserMsg>"
  (cl:format cl:nil "string name~%string username~%int64 age~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'GameUserMsg)))
  "Returns full string definition for message of type 'GameUserMsg"
  (cl:format cl:nil "string name~%string username~%int64 age~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <GameUserMsg>))
  (cl:+ 0
     4 (cl:length (cl:slot-value msg 'name))
     4 (cl:length (cl:slot-value msg 'username))
     8
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <GameUserMsg>))
  "Converts a ROS message object to a list"
  (cl:list 'GameUserMsg
    (cl:cons ':name (name msg))
    (cl:cons ':username (username msg))
    (cl:cons ':age (age msg))
))
