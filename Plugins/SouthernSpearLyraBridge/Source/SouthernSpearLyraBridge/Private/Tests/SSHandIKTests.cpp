// Copyright Southern Spear. All Rights Reserved.
//
// Left-hand IK (W2): the pure two-bone solve on a component-space arm puts the hand on a reachable
// target, keeps bone lengths, keeps the hand's rotation, carries fingers and twist bones with their
// bones, stops at full reach, blends by alpha, and refuses a broken chain. The rotation step (Session
// 070) then turns the hand to the target's rotation and carries its descendants, so the palm follows
// the hold instead of lying open on the receiver. FSSGripHold builds that target from the weapon's own
// sockets (Session 073), so the hand is authored from the weapon rather than borrowed from a pose.

#include "Misc/AutomationTest.h"

#include "SSHandIKMeshComponent.h"

#if WITH_DEV_AUTOMATION_TESTS

namespace
{
	// root(0) -> clavicle(1) -> upperarm(2) -> lowerarm(3) -> hand(4) -> finger(5); upperarm -> twist(6)
	void MakeArm(TArray<FTransform>& Pose, TArray<int32>& Parents)
	{
		Parents = { INDEX_NONE, 0, 1, 2, 3, 4, 2 };
		const FQuat HandRot = FQuat(FVector(0, 0, 1), FMath::DegreesToRadians(20.f));
		Pose = {
			FTransform(FVector(0, 0, 0)),
			FTransform(FVector(0, 10, 140)),
			FTransform(FVector(0, 20, 140)),
			FTransform(FQuat::Identity, FVector(0, 48, 130)),   // elbow: 29.7 cm, bent down and out
			FTransform(HandRot, FVector(20, 60, 115)),          // wrist: 26.0 cm on
			FTransform(HandRot, FVector(28, 62, 114)),          // a finger off the hand
			FTransform(FVector(0, 34, 135)),                    // upperarm twist
		};
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSHandIKSolveTest, "SouthernSpear.Bridge.HandIK.Solve",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSSHandIKSolveTest::RunTest(const FString& Parameters)
{
	TArray<FTransform> Pose;
	TArray<int32> Parents;
	MakeArm(Pose, Parents);
	const TArray<FTransform> Before = Pose;
	const double L1 = FVector::Distance(Before[2].GetLocation(), Before[3].GetLocation());
	const double L2 = FVector::Distance(Before[3].GetLocation(), Before[4].GetLocation());

	// A reachable target in front of the chest.
	const FVector Target(35.f, 30.f, 125.f);
	TestTrue(TEXT("solve applies"), FSSHandIK::Apply(Pose, Parents, 2, 3, 4, Target, 1.f));
	TestTrue(TEXT("hand on the target"), Pose[4].GetLocation().Equals(Target, 0.05f));
	TestTrue(TEXT("shoulder does not move"), Pose[2].GetLocation().Equals(Before[2].GetLocation(), 1e-3f));
	TestEqual(TEXT("upper arm length kept"), FVector::Distance(Pose[2].GetLocation(), Pose[3].GetLocation()), L1, 0.01);
	TestEqual(TEXT("forearm length kept"), FVector::Distance(Pose[3].GetLocation(), Pose[4].GetLocation()), L2, 0.01);
	TestTrue(TEXT("hand keeps its animated rotation"), Pose[4].GetRotation().Equals(Before[4].GetRotation(), 1e-4f));
	TestTrue(TEXT("finger carried with the hand"),
		Pose[5].GetRelativeTransform(Pose[4]).Equals(Before[5].GetRelativeTransform(Before[4]), 1e-3f));
	TestTrue(TEXT("twist bone carried with the upper arm"),
		Pose[6].GetRelativeTransform(Pose[2]).Equals(Before[6].GetRelativeTransform(Before[2]), 1e-3f));
	TestTrue(TEXT("bones outside the arm untouched"), Pose[1].Equals(Before[1], 1e-6f) && Pose[0].Equals(Before[0], 1e-6f));
	// The upper arm's own axis now points at the new elbow (the bone rotation matches its child's position).
	const FVector UpperAxisBefore = Before[2].GetRotation().UnrotateVector(Before[3].GetLocation() - Before[2].GetLocation());
	const FVector UpperAxisAfter = Pose[2].GetRotation().UnrotateVector(Pose[3].GetLocation() - Pose[2].GetLocation());
	TestTrue(TEXT("elbow stays on the upper arm's axis"), UpperAxisBefore.Equals(UpperAxisAfter, 0.01f));
	const FVector LowerAxisBefore = Before[3].GetRotation().UnrotateVector(Before[4].GetLocation() - Before[3].GetLocation());
	const FVector LowerAxisAfter = Pose[3].GetRotation().UnrotateVector(Pose[4].GetLocation() - Pose[3].GetLocation());
	TestTrue(TEXT("wrist stays on the forearm's axis"), LowerAxisBefore.Equals(LowerAxisAfter, 0.01f));

	// Out of reach: the hand stops at full reach along the line, no stretching.
	MakeArm(Pose, Parents);
	const FVector Far(200.f, 20.f, 140.f);
	TestTrue(TEXT("far solve applies"), FSSHandIK::Apply(Pose, Parents, 2, 3, 4, Far, 1.f));
	const double Reach = FVector::Distance(Pose[2].GetLocation(), Pose[4].GetLocation());
	TestTrue(TEXT("full reach, not stretched"), Reach <= L1 + L2 + 0.01 && Reach >= L1 + L2 - 0.05);
	TestTrue(TEXT("pointing at the far target"),
		((Pose[4].GetLocation() - Pose[2].GetLocation()).GetSafeNormal() | (Far - Pose[2].GetLocation()).GetSafeNormal()) > 0.9999);

	// Alpha: half-way blends the effector half-way.
	MakeArm(Pose, Parents);
	FSSHandIK::Apply(Pose, Parents, 2, 3, 4, Target, 0.5f);
	TestTrue(TEXT("alpha 0.5 lands half-way"), Pose[4].GetLocation().Equals(FMath::Lerp(Before[4].GetLocation(), Target, 0.5f), 0.05f));

	// Refusals leave the pose untouched.
	MakeArm(Pose, Parents);
	TestFalse(TEXT("alpha 0 does nothing"), FSSHandIK::Apply(Pose, Parents, 2, 3, 4, Target, 0.f));
	TestFalse(TEXT("a broken chain is refused"), FSSHandIK::Apply(Pose, Parents, 2, 6, 4, Target, 1.f));
	TestFalse(TEXT("mismatched parents are refused"), FSSHandIK::Apply(Pose, TArray<int32>{ INDEX_NONE }, 2, 3, 4, Target, 1.f));
	bool bSame = true;
	for (int32 Bone = 0; Bone < Pose.Num(); ++Bone)
	{
		bSame &= Pose[Bone].Equals(Before[Bone], 1e-6f);
	}
	TestTrue(TEXT("refusals leave the pose as it was"), bSame);
	return true;
}

// The hand's rotation step: a wrist-only solve leaves the palm open, so the hand is turned to the
// grip's hold rotation (hold * per-skeleton offset) and everything under the hand follows.
// The hold the left hand takes on a weapon, built from the weapon's own sockets (Session 073). No world:
// a synthetic bore, and the frame it must produce.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSGripHoldTest, "SouthernSpear.Bridge.HandIK.GripHold",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSSGripHoldTest::RunTest(const FString& Parameters)
{
	auto Det3 = [](const FVector& A, const FVector& B, const FVector& C)
	{
		return FVector::DotProduct(A, FVector::CrossProduct(B, C));
	};

	// A weapon lying along +X with its up on +Z, muzzle 40 cm ahead of the trigger hand.
	const FVector RightHandGrip(0.0, 0.0, 0.0);
	const FVector Muzzle(40.0, 0.0, 0.0);
	FSSGripHold Hold;
	TestTrue(TEXT("hold builds"), FSSHandIK::BuildGripHold(Muzzle, RightHandGrip, FVector::UpVector, 30.f, Hold));

	// The weapon's own basis: the thumb lies on the bore, and the sign of right is the one the weapon
	// shows - the ejection port is on +Right, the left hand grip on -Right (UE satisfies F x R = U).
	TestTrue(TEXT("thumb on the bore"), Hold.Thumb.Equals(Hold.Forward, 1e-4f));
	TestTrue(TEXT("forward is the bore"), Hold.Forward.Equals(FVector(1, 0, 0), 1e-4f));
	TestTrue(TEXT("up is the weapon's up, orthogonal to the bore"), Hold.Up.Equals(FVector(0, 0, 1), 1e-4f));
	TestTrue(TEXT("right is the weapon's right"), Hold.Right.Equals(FVector(0, 1, 0), 1e-4f));
	TestEqual(TEXT("the weapon basis is right-handed"), Det3(Hold.Forward, Hold.Right, Hold.Up), 1.0, 1e-4);

	// The hold: the palm is the up, tilted 30 degrees towards the right, and nothing else moves.
	const FVector ExpectedPalm = FVector(0, 0.5, FMath::Sqrt(0.75));
	TestTrue(TEXT("palm tilted 30 deg off the weapon's up towards right"), Hold.Palm.Equals(ExpectedPalm, 1e-4f));
	TestEqual(TEXT("the palm is 30 deg off up"), FMath::RadiansToDegrees(FMath::Acos(Hold.Palm.Dot(Hold.Up))), 30.0, 0.01);
	TestTrue(TEXT("the palm leans towards right, not left"), Hold.Palm.Dot(Hold.Right) > 0.f);
	TestTrue(TEXT("palm is perpendicular to the bore"), FMath::Abs(Hold.Palm.Dot(Hold.Forward)) < 1e-4f);
	TestTrue(TEXT("finger = palm x thumb (the left hand's order)"),
		Hold.Finger.Equals(FVector::CrossProduct(Hold.Palm, Hold.Thumb), 1e-4f));
	// A left hand: palm = thumb x finger. The opposite order, thumb x palm, is a RIGHT hand's and authors a
	// mirrored fist - which still matched its own target to 0.0 deg and rendered upside down on the tube.
	TestTrue(TEXT("palm = thumb x finger (left hand)"),
		FVector::CrossProduct(Hold.Thumb, Hold.Finger).Equals(Hold.Palm, 1e-3f));
	TestTrue(TEXT("palm x finger = -thumb: the hand's own triple is left-handed"),
		FVector::CrossProduct(Hold.Palm, Hold.Finger).Equals(-Hold.Thumb, 1e-3f));
	TestTrue(TEXT("not the right hand's order"),
		!FVector::CrossProduct(Hold.Finger, Hold.Thumb).Equals(Hold.Palm, 1e-3f));
	TestTrue(TEXT("the hand frame is orthonormal"),
		Hold.Palm.IsUnit() && Hold.Finger.IsUnit() && Hold.Thumb.IsUnit()
		&& FMath::Abs(Hold.Palm.Dot(Hold.Finger)) < 1e-4f
		&& FMath::Abs(Hold.Palm.Dot(Hold.Thumb)) < 1e-4f
		&& FMath::Abs(Hold.Finger.Dot(Hold.Thumb)) < 1e-4f);

	// The hand's basis: +X palm, +Y finger, and +Z the back-of-hand axis, because that triple is left-handed
	// and so is not a rotation. -Thumb is the axis that makes it one.
	const FQuat AsHand = Hold.ToHandRotation();
	TestTrue(TEXT("ToHandRotation carries +X to the palm"), AsHand.RotateVector(FVector(1, 0, 0)).Equals(Hold.Palm, 1e-3f));
	TestTrue(TEXT("ToHandRotation carries +Y to the finger"), AsHand.RotateVector(FVector(0, 1, 0)).Equals(Hold.Finger, 1e-3f));
	TestTrue(TEXT("ToHandRotation carries +Z to the back of the hand (-thumb)"),
		AsHand.RotateVector(FVector(0, 0, 1)).Equals(-Hold.Thumb, 1e-3f));
	TestEqual(TEXT("the hand basis is a proper rotation"), Det3(Hold.Palm, Hold.Finger, -Hold.Thumb), 1.0, 1e-3);

	// A vertical grip: 90 deg puts the palm flat across the weapon's right, fingers wrapping it.
	FSSGripHold Vertical;
	TestTrue(TEXT("vertical hold builds"), FSSHandIK::BuildGripHold(Muzzle, RightHandGrip, FVector::UpVector, 90.f, Vertical));
	TestTrue(TEXT("at 90 deg the palm faces right"), Vertical.Palm.Equals(FVector(0, 1, 0), 1e-4f));
	TestTrue(TEXT("at 90 deg the thumb still lies on the bore"), Vertical.Thumb.Equals(Hold.Thumb, 1e-4f));
	TestTrue(TEXT("at 90 deg the frame is still the left hand's"),
		FVector::CrossProduct(Vertical.Thumb, Vertical.Finger).Equals(Vertical.Palm, 1e-3f));
	// A flat hand under the handguard: 0 deg.
	FSSGripHold Flat;
	TestTrue(TEXT("flat hold builds"), FSSHandIK::BuildGripHold(Muzzle, RightHandGrip, FVector::UpVector, 0.f, Flat));
	TestTrue(TEXT("at 0 deg the palm is the weapon's up"), Flat.Palm.Equals(FVector(0, 0, 1), 1e-4f));

	// The frame follows a weapon that is not axis-aligned: the bore swung across the up axis.
	const FVector MuzzleA = (FVector(1, 0, 0) * 0.8 + FVector(0, 1, 0) * 0.35).GetSafeNormal() * 40.0;
	FSSGripHold Slanted;
	TestTrue(TEXT("slanted hold builds"),
		FSSHandIK::BuildGripHold(MuzzleA, RightHandGrip, FVector::UpVector, 30.f, Slanted));
	TestTrue(TEXT("the thumb still lies on the bore"), Slanted.Thumb.Equals(Slanted.Forward, 1e-4f));
	TestTrue(TEXT("up stays orthogonal to the bore"), FMath::Abs(Slanted.Up.Dot(Slanted.Forward)) < 1e-4f);
	TestTrue(TEXT("up is the weapon's up, orthogonalised"), Slanted.Up.Dot(FVector::UpVector) > 0.99f);
	TestTrue(TEXT("palm still leans towards right"), Slanted.Palm.Dot(Slanted.Right) > 0.49f && Slanted.Palm.Dot(Slanted.Right) < 0.51f);
	TestTrue(TEXT("palm = thumb x finger on a slanted weapon too"),
		FVector::CrossProduct(Slanted.Thumb, Slanted.Finger).Equals(Slanted.Palm, 1e-3f));
	TestEqual(TEXT("the slanted hand basis is a proper rotation"), Det3(Slanted.Palm, Slanted.Finger, -Slanted.Thumb), 1.0, 1e-3);

	// The nudge: the wrist target moves along the hold's OWN axes, so a per-weapon centimetre value
	// means the same thing whatever the mesh is doing (Session 074, R-86).
	const FVector Target(0.0, -12.0, 1.0);          // a socket well off the bore, on the weapon's left
	FSSGripNudge Nudge;
	TestTrue(TEXT("a zero nudge leaves the target alone"),
		FSSHandIK::ApplyGripNudge(Hold, Target, Nudge).Equals(Target, 1e-4f));
	Nudge.Forward = 1.f;
	Nudge.Right = 2.f;
	Nudge.Up = -3.f;
	const FVector Nudged = FSSHandIK::ApplyGripNudge(Hold, Target, Nudge);
	TestTrue(TEXT("the nudge moves the target along forward, right and up"),
		Nudged.Equals(Target + Hold.Forward * 1.f + Hold.Right * 2.f + Hold.Up * -3.f, 1e-4f));
	// Against the synthetic hold (forward +X, right +Y, up +Z) the nudge is read straight off.
	TestTrue(TEXT("right moves towards the weapon's right, up moves along its up"),
		Nudged.Equals(FVector(1.f, -10.0, -2.0), 1e-4f));
	TestEqual(TEXT("the nudge's length is the centimetres asked for"),
		FVector::Distance(Nudged, Target), FMath::Sqrt(14.0), 1e-3);
	// The nudge is position only: it must not touch the hold's rotation, or the solved offset drifts.
	TestTrue(TEXT("a nudge leaves the hold's own frame untouched"),
		Hold.Forward.Equals(FVector(1, 0, 0), 1e-4f) && Hold.Right.Equals(FVector(0, 1, 0), 1e-4f)
		&& Hold.Up.Equals(FVector(0, 0, 1), 1e-4f) && Hold.Thumb.Equals(FVector(1, 0, 0), 1e-4f));

	// Refusals: no bore, or the weapon's up along it, leave no frame to hold, and the caller is told.
	Hold = Vertical;   // a hold the caller already had, which a refusal must not leave behind
	TestFalse(TEXT("coincident sockets are refused"),
		FSSHandIK::BuildGripHold(RightHandGrip, RightHandGrip, FVector::UpVector, 30.f, Hold));
	TestFalse(TEXT("an up vector along the bore is refused"),
		FSSHandIK::BuildGripHold(Muzzle, RightHandGrip, FVector(1, 0, 0), 30.f, Hold));
	TestTrue(TEXT("a refused build zeroes the hold rather than leaving a stale one"),
		Hold.Forward.IsNearlyZero() && Hold.Palm.IsNearlyZero()
		&& Hold.Finger.IsNearlyZero() && Hold.Thumb.IsNearlyZero());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSSHandIKRotateTest, "SouthernSpear.Bridge.HandIK.RotateHand",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FSSHandIKRotateTest::RunTest(const FString& Parameters)
{
	TArray<FTransform> Pose;
	TArray<int32> Parents;
	const FQuat Target = FRotator(35.f, -20.f, 70.f).Quaternion();

	// At alpha 1 the hand's rotation is the target's, and its position is left alone.
	MakeArm(Pose, Parents);
	const TArray<FTransform> Before = Pose;
	TestTrue(TEXT("rotate applies"), FSSHandIK::RotateChain(Pose, Parents, 4, Target, 1.f));
	TestTrue(TEXT("the hand matches the target at alpha 1"), Pose[4].GetRotation().Equals(Target, 1e-4f));
	TestTrue(TEXT("the hand keeps the position the solve gave it"), Pose[4].GetLocation().Equals(Before[4].GetLocation(), 1e-6f));
	TestTrue(TEXT("a finger follows with its own local transform"),
		Pose[5].GetRelativeTransform(Pose[4]).Equals(Before[5].GetRelativeTransform(Before[4]), 1e-5f));
	TestTrue(TEXT("bones outside the hand are untouched"),
		Pose[0].Equals(Before[0], 1e-6f) && Pose[1].Equals(Before[1], 1e-6f)
			&& Pose[2].Equals(Before[2], 1e-6f) && Pose[3].Equals(Before[3], 1e-6f)
			&& Pose[6].Equals(Before[6], 1e-6f));

	// Both steps together: the hand is on the grip with the grip's rotation (what the component does).
	MakeArm(Pose, Parents);
	const FVector TargetLocation(35.f, 30.f, 125.f);
	TestTrue(TEXT("solve then rotate both apply"),
		FSSHandIK::Apply(Pose, Parents, 2, 3, 4, TargetLocation, 1.f)
			&& FSSHandIK::RotateChain(Pose, Parents, 4, Target, 1.f));
	TestTrue(TEXT("hand on the grip"), Pose[4].GetLocation().Equals(TargetLocation, 0.05f));
	TestTrue(TEXT("hand turned to the grip"), Pose[4].GetRotation().Equals(Target, 1e-4f));

	// Alpha blends the rotation the same way it blends the position.
	MakeArm(Pose, Parents);
	FSSHandIK::RotateChain(Pose, Parents, 4, Target, 0.5f);
	TestTrue(TEXT("alpha 0.5 is half-way round"),
		Pose[4].GetRotation().Equals(FQuat::Slerp(Before[4].GetRotation(), Target, 0.5f), 1e-4f));

	// A zero offset (the config default) reproduces the hold's own rotation exactly.
	MakeArm(Pose, Parents);
	const FQuat HoldRotation = FRotator(12.f, 88.f, -3.f).Quaternion();
	const FQuat WithOffset = HoldRotation * FRotator::ZeroRotator.Quaternion();
	FSSHandIK::RotateChain(Pose, Parents, 4, WithOffset, 1.f);
	TestTrue(TEXT("a zero offset keeps the hold's own rotation"), Pose[4].GetRotation().Equals(HoldRotation, 1e-4f));

	// Refusals leave the pose untouched.
	MakeArm(Pose, Parents);
	TestFalse(TEXT("alpha 0 does nothing"), FSSHandIK::RotateChain(Pose, Parents, 4, Target, 0.f));
	TestFalse(TEXT("a bad hand index is refused"), FSSHandIK::RotateChain(Pose, Parents, 99, Target, 1.f));
	TestFalse(TEXT("mismatched parents are refused"),
		FSSHandIK::RotateChain(Pose, TArray<int32>{ INDEX_NONE }, 4, Target, 1.f));
	bool bSame = true;
	for (int32 Bone = 0; Bone < Pose.Num(); ++Bone)
	{
		bSame &= Pose[Bone].Equals(Before[Bone], 1e-6f);
	}
	TestTrue(TEXT("refusals leave the pose as it was"), bSame);
	return true;
}

#endif
