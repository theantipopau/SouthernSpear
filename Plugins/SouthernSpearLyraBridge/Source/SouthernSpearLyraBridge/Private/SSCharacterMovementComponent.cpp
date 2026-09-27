// Copyright Southern Spear. All Rights Reserved.

#include "SSCharacterMovementComponent.h"

#include "GameFramework/Character.h"

namespace
{
	// Custom compressed flags (FSavedMove_Character::FLAG_Custom_0..2).
	constexpr uint8 FlagSprint = FSavedMove_Character::FLAG_Custom_0;
	constexpr uint8 FlagWalk = FSavedMove_Character::FLAG_Custom_1;
	constexpr uint8 FlagAim = FSavedMove_Character::FLAG_Custom_2;

	class FSavedMove_SS : public FSavedMove_Character
	{
	public:
		virtual void Clear() override
		{
			FSavedMove_Character::Clear();
			bSprint = bWalk = bAim = false;
		}

		virtual uint8 GetCompressedFlags() const override
		{
			uint8 Flags = FSavedMove_Character::GetCompressedFlags();
			if (bSprint) { Flags |= FlagSprint; }
			if (bWalk) { Flags |= FlagWalk; }
			if (bAim) { Flags |= FlagAim; }
			return Flags;
		}

		virtual bool CanCombineWith(const FSavedMovePtr& NewMove, ACharacter* InCharacter, float MaxDelta) const override
		{
			const FSavedMove_SS* Other = static_cast<const FSavedMove_SS*>(NewMove.Get());
			if (bSprint != Other->bSprint || bWalk != Other->bWalk || bAim != Other->bAim)
			{
				return false;
			}
			return FSavedMove_Character::CanCombineWith(NewMove, InCharacter, MaxDelta);
		}

		virtual void SetMoveFor(ACharacter* C, float InDeltaTime, FVector const& NewAccel, FNetworkPredictionData_Client_Character& ClientData) override
		{
			FSavedMove_Character::SetMoveFor(C, InDeltaTime, NewAccel, ClientData);
			if (const USSCharacterMovementComponent* Movement = Cast<USSCharacterMovementComponent>(C->GetCharacterMovement()))
			{
				bSprint = Movement->WantsSprint();
				bWalk = Movement->WantsWalk();
				bAim = Movement->WantsAim();
			}
		}

		virtual void PrepMoveFor(ACharacter* C) override
		{
			FSavedMove_Character::PrepMoveFor(C);
			if (USSCharacterMovementComponent* Movement = Cast<USSCharacterMovementComponent>(C->GetCharacterMovement()))
			{
				Movement->SetWantsSprint(bSprint);
				Movement->SetWantsWalk(bWalk);
				Movement->SetWantsAim(bAim);
			}
		}

	private:
		bool bSprint = false;
		bool bWalk = false;
		bool bAim = false;
	};

	class FNetworkPredictionData_Client_SS : public FNetworkPredictionData_Client_Character
	{
	public:
		explicit FNetworkPredictionData_Client_SS(const UCharacterMovementComponent& ClientMovement)
			: FNetworkPredictionData_Client_Character(ClientMovement)
		{
		}

		virtual FSavedMovePtr AllocateNewMove() override
		{
			return FSavedMovePtr(new FSavedMove_SS());
		}
	};
}

USSCharacterMovementComponent::USSCharacterMovementComponent(const FObjectInitializer& ObjectInitializer)
	: Super(ObjectInitializer)
{
	ApplyTuning();
}

void USSCharacterMovementComponent::InitializeComponent()
{
	Super::InitializeComponent();
	// Lyra's hero Blueprints override movement values (acceleration 1200, braking 1400, friction 8);
	// the tactical tuning wins at runtime.
	ApplyTuning();
}

void USSCharacterMovementComponent::ApplyTuning()
{
	MaxWalkSpeed = Tuning.JogSpeed;
	MaxWalkSpeedCrouched = Tuning.CrouchSpeed;
	MaxAcceleration = Tuning.Acceleration;
	BrakingDecelerationWalking = Tuning.BrakingDeceleration;
	GroundFriction = Tuning.GroundFriction;
	bUseSeparateBrakingFriction = true;
	BrakingFriction = 2.f;
	AirControl = Tuning.AirControl;
	JumpZVelocity = Tuning.JumpZVelocity;
}

ESSStance USSCharacterMovementComponent::GetStance() const
{
	return IsCrouching() ? ESSStance::Crouch : ESSStance::Stand;
}

ESSGait USSCharacterMovementComponent::GetGait() const
{
	const FVector Accel = GetCurrentAcceleration();
	FVector2D Local = FVector2D::ZeroVector;
	if (UpdatedComponent && !Accel.IsNearlyZero())
	{
		const FVector L = UpdatedComponent->GetComponentTransform().InverseTransformVectorNoScale(Accel);
		Local = FVector2D(L.X, L.Y);
	}
	return FSSMovementRules::ResolveGait(bWantsSprint, bWantsWalk, GetStance(), bWantsAim, Local, Tuning);
}

float USSCharacterMovementComponent::GetMaxSpeed() const
{
	const float LyraSpeed = Super::GetMaxSpeed(); // 0 while Lyra's "movement stopped" tag is on
	if (LyraSpeed <= 0.f || !IsMovingOnGround())
	{
		return LyraSpeed;
	}
	return FSSMovementRules::MaxSpeed(GetGait(), GetStance(), bWantsAim, Tuning);
}

void USSCharacterMovementComponent::UpdateFromCompressedFlags(uint8 Flags)
{
	Super::UpdateFromCompressedFlags(Flags);
	bWantsSprint = (Flags & FlagSprint) != 0;
	bWantsWalk = (Flags & FlagWalk) != 0;
	bWantsAim = (Flags & FlagAim) != 0;
}

FNetworkPredictionData_Client* USSCharacterMovementComponent::GetPredictionData_Client() const
{
	if (!ClientPredictionData)
	{
		USSCharacterMovementComponent* Mutable = const_cast<USSCharacterMovementComponent*>(this);
		Mutable->ClientPredictionData = new FNetworkPredictionData_Client_SS(*this);
	}
	return ClientPredictionData;
}
